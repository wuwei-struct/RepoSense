import json
import os

from .drilldown_schema import build_request, normalize_snippet_pack
from .snippet_selector import select_candidates


def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _read_text_lines(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    except Exception:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read().splitlines()
        except Exception:
            return None


def _safe_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return int(default)


def _detect_language(path):
    ext = os.path.splitext(str(path or "").lower())[1]
    m = {
        ".py": "python",
        ".java": "java",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".sql": "sql",
        ".yaml": "yaml",
        ".yml": "yaml",
    }
    return m.get(ext, "unknown")


def _resolve_source_path(repo_root, rel_or_abs):
    p = str(rel_or_abs or "")
    if not p:
        return ""
    if os.path.isabs(p):
        return p
    return os.path.join(repo_root, p)


def _load_facts(run_dir):
    report = _read_json(os.path.join(run_dir, "report.json"), {})
    graph = _read_json(os.path.join(run_dir, "event_graph.json"), {"nodes": [], "edges": []})
    patterns_obj = _read_json(os.path.join(run_dir, "patterns.json"), {"patterns": []})
    manifest = _read_json(os.path.join(run_dir, "manifest.json"), {})
    repo_root = str(manifest.get("repo_root") or run_dir)
    return {
        "repo_root": repo_root,
        "findings": report.get("findings") or [],
        "events": graph.get("nodes") or [],
        "patterns": patterns_obj.get("patterns") if isinstance(patterns_obj, dict) else [],
    }


def generate_snippet_pack(run_dir, target_type, target_id, budget=None):
    req = build_request(target_type, target_id, budget=budget)
    facts = _load_facts(run_dir)
    picked = select_candidates(facts, req)
    candidates = picked.get("candidates") or []
    limitations = [
        "No full-repo source scan was performed.",
        "Snippets were selected only from facts/evidence references and local context windows.",
        "Conclusions may require follow-up review.",
    ]
    snippets = []
    total_chars = 0
    missing_files = 0
    for idx, c in enumerate(candidates, start=1):
        file_rel = str(c.get("file") or "")
        src_path = _resolve_source_path(facts.get("repo_root") or run_dir, file_rel)
        lines = _read_text_lines(src_path)
        if lines is None:
            missing_files += 1
            limitations.append(f"File not readable or missing: {file_rel}")
            continue
        start = max(1, _safe_int(c.get("line_start"), 1))
        end = max(start, _safe_int(c.get("line_end"), start))
        if start > len(lines):
            limitations.append(f"Line range out of bounds in {file_rel}: {start}-{end}")
            continue
        end = min(end, len(lines))
        snippet_text = "\n".join(lines[start - 1 : end])
        add_chars = len(snippet_text)
        if total_chars + add_chars > _safe_int((req.get("budget") or {}).get("max_total_chars"), 12000):
            limitations.append("Total character budget reached; remaining snippets were skipped.")
            break
        total_chars += add_chars
        snippets.append(
            {
                "snippet_id": f"{req['request_id']}-s{idx}",
                "file": file_rel,
                "line_start": start,
                "line_end": end,
                "context_before": _safe_int(c.get("context_before"), 0),
                "context_after": _safe_int(c.get("context_after"), 0),
                "snippet": snippet_text,
                "language": _detect_language(file_rel),
                "why_selected": str(c.get("why_selected") or "evidence_ref_window"),
                "source_refs": c.get("source_refs") if isinstance(c.get("source_refs"), list) else [],
                "confidence": float(c.get("confidence") or 0.0),
            }
        )
    if missing_files > 0:
        limitations.append(f"{missing_files} file(s) could not be loaded from repo_root.")
    pack = normalize_snippet_pack(
        {
            "request_id": req["request_id"],
            "run_dir": run_dir,
            "target_type": req["target_type"],
            "target_id": req["target_id"],
            "selected_snippets": snippets,
            "budget": {**req["budget"], "total_chars": total_chars},
            "selection_trace": {
                **(picked.get("selection_trace") or {}),
                "repo_root": str(facts.get("repo_root") or ""),
                "loaded_snippets": len(snippets),
            },
            "limitations": sorted(set(limitations)),
        }
    )
    return pack
