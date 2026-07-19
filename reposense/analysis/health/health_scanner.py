import json
import os
import re

from .health_rules import DEFAULT_THRESHOLDS, SKIP_DIRS, SOURCE_EXTENSIONS, is_core_path, is_generated_or_config, is_test_path
from .health_schema import normalize_health_finding
from ..context.file_context import apply_file_context, classify_file_contexts


DEBT_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX|workaround)\b|临时|先这样|不要删", re.IGNORECASE)
TS_ESCAPE_RE = re.compile(r"(@ts-ignore|@ts-expect-error|\bas\s+any\b|:\s*any\b|\bunknown\s+as\b)")
PY_ESCAPE_RE = re.compile(r"#\s*type:\s*ignore")


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _rel(root, path):
    return os.path.relpath(path, root).replace("\\", "/")


def _iter_source_files(repo_path):
    root = os.path.abspath(repo_path)
    for cur, dirs, files in os.walk(root):
        dirs[:] = [
            d
            for d in dirs
            if d not in SKIP_DIRS
            and not d.startswith(".reposense_")
            and d not in {"analysis_runs", ".mypy_cache"}
        ]
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext not in SOURCE_EXTENSIONS:
                continue
            path = os.path.join(cur, name)
            rel = _rel(root, path)
            if is_generated_or_config(rel):
                continue
            yield rel, path


def _evidence(rule_id, file_path, line_start, line_end, snippet):
    return [
        {
            "source_type": "code_health",
            "rule_id": rule_id,
            "file": file_path,
            "start_line": int(line_start or 1),
            "end_line": int(line_end or line_start or 1),
            "snippet": snippet,
        }
    ]


def _finding(rule_id, title, severity, status, confidence, file_path, line_start, line_end, snippet, signals, reason, metadata=None):
    return normalize_health_finding(
        {
            "rule_id": rule_id,
            "title": title,
            "severity": severity,
            "status": status,
            "confidence": confidence,
            "file": file_path,
            "line_start": line_start,
            "line_end": line_end,
            "snippet": snippet,
            "signals": signals,
            "reason": reason,
            "evidence_refs": _evidence(rule_id, file_path, line_start, line_end, snippet),
            "metadata": metadata or {},
        }
    )


def _scan_file_size(rel, lines, thresholds):
    count = len(lines)
    giant = int(thresholds.get("giant_file_lines") or DEFAULT_THRESHOLDS["giant_file_lines"])
    large = int(thresholds.get("large_file_lines") or DEFAULT_THRESHOLDS["large_file_lines"])
    if count >= giant:
        return _finding(
            "CHD-001",
            "Giant file",
            "medium",
            "confirmed",
            0.85,
            rel,
            1,
            count,
            f"{count} lines",
            ["giant_file"],
            "File size exceeds the giant file threshold and may require human maintainability review.",
            {"line_count": count, "threshold": giant},
        )
    if count >= large:
        return _finding(
            "CHD-001",
            "Large file",
            "low",
            "confirmed",
            0.75,
            rel,
            1,
            count,
            f"{count} lines",
            ["large_file"],
            "File size exceeds the large file threshold; this is a maintainability signal, not a correctness proof.",
            {"line_count": count, "threshold": large},
        )
    return None


def _scan_debt_comments(rel, lines):
    out = []
    for idx, line in enumerate(lines, 1):
        m = DEBT_RE.search(line)
        if not m:
            continue
        token = (m.group(0) or "").lower()
        sev = "medium" if token in {"fixme", "hack", "workaround", "临时", "不要删"} else "low"
        out.append(
            _finding(
                "CHD-002",
                "Debt comment",
                sev,
                "confirmed",
                0.9,
                rel,
                idx,
                idx,
                line.strip(),
                ["debt_comment", token],
                "Debt-style comment observed in code.",
            )
        )
    return out


def _scan_type_escape(rel, lines):
    out = []
    ext = os.path.splitext(rel.lower())[1]
    regex = PY_ESCAPE_RE if ext == ".py" else TS_ESCAPE_RE
    if ext not in {".py", ".js", ".jsx", ".ts", ".tsx"}:
        return out
    for idx, line in enumerate(lines, 1):
        m = regex.search(line)
        if not m:
            continue
        sev = "low" if is_test_path(rel) else ("medium" if is_core_path(rel) else "low")
        out.append(
            _finding(
                "CHD-003",
                "Type escape",
                sev,
                "confirmed",
                0.88,
                rel,
                idx,
                idx,
                line.strip(),
                ["type_escape", m.group(0)],
                "Explicit type-system escape observed; review whether it is still needed.",
            )
        )
    return out


def _block_has_safe_handling(block):
    text = "\n".join(block).lower()
    return any(x in text for x in ["logger", "log.", "console.error", "throw", "raise", "retry", "compensat"])


def _scan_swallowed_errors(rel, lines):
    out = []
    ext = os.path.splitext(rel.lower())[1]
    if ext == ".py":
        for idx, line in enumerate(lines, 1):
            if not re.match(r"\s*except\b.*:\s*$", line):
                continue
            block = lines[idx : min(len(lines), idx + 6)]
            nonblank = [x.strip() for x in block if x.strip()]
            if _block_has_safe_handling(block):
                continue
            if nonblank and nonblank[0] in {"pass", "return None"}:
                out.append(
                    _finding("CHD-004", "Swallowed error", "medium", "confirmed", 0.82, rel, idx, idx, line.strip(), ["swallowed_error"], "Exception handler appears to swallow the error without logging, retry, compensation, or rethrow.")
                )
        return out
    if ext not in {".js", ".jsx", ".ts", ".tsx", ".java"}:
        return out
    for idx, line in enumerate(lines, 1):
        if "catch" not in line:
            continue
        block = lines[idx - 1 : min(len(lines), idx + 8)]
        text = "\n".join(block)
        if _block_has_safe_handling(block):
            continue
        compact = re.sub(r"\s+", " ", text)
        if re.search(r"catch\s*\([^)]*\)\s*\{\s*\}", compact) or re.search(r"catch\s*\([^)]*\)\s*\{\s*return\s+(null|undefined|false)\s*;?\s*\}", compact):
            out.append(
                _finding("CHD-004", "Swallowed error", "medium", "confirmed", 0.82, rel, idx, idx, line.strip(), ["swallowed_error"], "Catch block appears to swallow the error without logging, retry, compensation, or rethrow.")
            )
    return out


def _event_files_without_tests(run_dir, repo_path):
    graph = _read_json(os.path.join(run_dir, "event_graph.json"), {"nodes": []})
    nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []
    candidate_files = {}
    for n in nodes:
        if str(n.get("type") or "") not in {"api", "db_op", "tx_boundary", "queue_dispatch", "cache_op"}:
            continue
        meta = n.get("meta") if isinstance(n.get("meta"), dict) else {}
        path = str(meta.get("path") or meta.get("file") or "").replace("\\", "/")
        if not path:
            continue
        candidate_files.setdefault(path, {"line": int(meta.get("start_line") or 1), "signals": set()})
        candidate_files[path]["signals"].add(str(n.get("type") or "backend_event"))
    if not candidate_files:
        return []
    tests = []
    contents = {}
    for rel, path in _iter_source_files(repo_path):
        if is_test_path(rel):
            tests.append(rel)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    contents[rel] = f.read().lower()
            except Exception:
                contents[rel] = ""
    findings = []
    test_names = [t.lower() for t in tests]
    for file_path, info in sorted(candidate_files.items()):
        base = os.path.splitext(os.path.basename(file_path))[0]
        stem = re.sub(r"[^a-zA-Z0-9]+", "", base).lower()
        snake = re.sub(r"(?<!^)(?=[A-Z])", "_", base).lower()
        matched = False
        for t in test_names:
            tb = os.path.basename(t)
            if f"test_{base.lower()}" in tb or f"{base.lower()}_test" in tb or f"{base.lower()}.test" in tb or f"{base.lower()}.spec" in tb:
                matched = True
                break
            if stem and (stem in tb.replace("_", "").replace("-", "") or stem in contents.get(t, "")):
                matched = True
                break
            if snake and snake in tb:
                matched = True
                break
        if not matched:
            signals = sorted(info["signals"])
            findings.append(
                _finding(
                    "CHD-005",
                    "Backend side-effect file without adjacent test evidence",
                    "medium",
                    "suspected",
                    0.62,
                    file_path,
                    int(info.get("line") or 1),
                    int(info.get("line") or 1),
                    ", ".join(signals),
                    ["no_adjacent_test_evidence"] + signals,
                    "Backend side-effect signal observed, but no adjacent test evidence was found by conservative file-name matching.",
                    {"test_gap_policy": "file-name inference only"},
                )
            )
    return findings


def scan_code_health(run_dir, repo_path, thresholds=None):
    thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    findings = []
    root = os.path.abspath(repo_path)
    for rel, path in _iter_source_files(root):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.read().splitlines()
        except OSError:
            continue
        size_finding = _scan_file_size(rel, lines, thresholds)
        if size_finding:
            findings.append(size_finding)
        findings.extend(_scan_debt_comments(rel, lines))
        findings.extend(_scan_type_escape(rel, lines))
        findings.extend(_scan_swallowed_errors(rel, lines))
    findings.extend(_event_files_without_tests(run_dir, root))
    annotations = classify_file_contexts(root, extra_paths=[finding.get("file") for finding in findings])
    findings = apply_file_context(findings, annotations)
    findings.sort(key=lambda f: (f.get("rule_id"), f.get("file"), int(f.get("line_start") or 0), f.get("health_id")))
    return findings
