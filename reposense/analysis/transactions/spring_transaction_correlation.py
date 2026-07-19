from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from ...evidence.location import canonicalize_evidence_ref
from .correlation_schema import make_correlation_id, stable_sort_correlations


WRITE_METHODS = {
    "save", "saveAll", "delete", "deleteById", "deleteAll", "persist", "merge",
    "remove", "flush", "insert", "update", "executeUpdate",
}
RECEIVER_TYPES = {"EntityManager", "JdbcTemplate", "NamedParameterJdbcTemplate", "SqlSession"}
IGNORED_DIRS = {".git", ".venv", "node_modules", "build", "dist", "target", "out", "__pycache__"}


def _read_json(path, default):
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return default


def _simple_type(value):
    raw = re.sub(r"<.*>", "", str(value or "")).strip()
    return raw.replace("[]", "").split(".")[-1].strip()


def _is_receiver_type(value):
    name = _simple_type(value)
    return (
        name in RECEIVER_TYPES
        or name.endswith("Repository")
        or name.endswith("RepositoryOverride")
        or name.endswith("Dao")
        or name.endswith("DAO")
    )


def _strip_comments(lines):
    result = []
    in_block = False
    for raw in lines:
        out = []
        i = 0
        while i < len(raw):
            if in_block:
                end = raw.find("*/", i)
                if end < 0:
                    i = len(raw)
                    continue
                in_block = False
                i = end + 2
                continue
            start = raw.find("/*", i)
            slashes = raw.find("//", i)
            if slashes >= 0 and (start < 0 or slashes < start):
                out.append(raw[i:slashes])
                break
            if start < 0:
                out.append(raw[i:])
                break
            out.append(raw[i:start])
            in_block = True
            i = start + 2
        result.append("".join(out))
    return result


def _transaction_annotation(annotations):
    for annotation in reversed(annotations or []):
        text = str(annotation.get("text") or "")
        if re.search(r"@(?:[A-Za-z0-9_$.]+\.)?Transactional\b", text):
            return {
                "present": True,
                "read_only": bool(re.search(r"readOnly\s*=\s*true", text, flags=re.I)),
                "line": int(annotation.get("line") or 0),
                "text": text.strip(),
            }
    return {"present": False, "read_only": False, "line": None, "text": ""}


def _method_name(line):
    text = line.strip()
    if not text or ";" in text or "(" not in text or "{" not in text:
        return ""
    if re.match(r"^(if|for|while|switch|catch|try|synchronized)\b", text):
        return ""
    prefix = text.split("(", 1)[0].strip()
    if "=" in prefix:
        return ""
    match = re.search(r"([A-Za-z_$][A-Za-z0-9_$]*)\s*$", prefix)
    return match.group(1) if match else ""


def _class_declaration(line):
    match = re.search(r"\b(class|interface)\s+([A-Za-z_$][A-Za-z0-9_$]*)([^\{]*)\{", line)
    if not match:
        return None
    tail = match.group(3) or ""
    parents = []
    parent_match = re.search(r"\b(?:implements|extends)\s+(.+)$", tail)
    if parent_match:
        parents = [_simple_type(x.strip()) for x in parent_match.group(1).split(",") if _simple_type(x.strip())]
    return {"kind": match.group(1), "name": match.group(2), "parents": parents}


def _field_receivers(code_lines, class_name):
    receivers = {}
    field_re = re.compile(
        r"^\s*(?:(?:public|protected|private)\s+)?(?:static\s+)?(?:final\s+)?"
        r"([A-Za-z_$][A-Za-z0-9_$.]*(?:<[^;=]+>)?)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*(?:=[^;]+)?;"
    )
    for line in code_lines:
        match = field_re.match(line)
        if match and _is_receiver_type(match.group(1)):
            receivers[match.group(2)] = _simple_type(match.group(1))
    joined = "\n".join(code_lines)
    constructor = re.search(rf"\b{re.escape(class_name)}\s*\((.*?)\)\s*\{{", joined, flags=re.S)
    if constructor:
        for param in constructor.group(1).split(","):
            cleaned = re.sub(r"@[A-Za-z0-9_$.]+(?:\([^)]*\))?", "", param).strip()
            match = re.search(r"([A-Za-z_$][A-Za-z0-9_$.]*(?:<[^>]+>)?)\s+([A-Za-z_$][A-Za-z0-9_$]*)$", cleaned)
            if match and _is_receiver_type(match.group(1)):
                receivers[match.group(2)] = _simple_type(match.group(1))
    return receivers


def _parse_java_file(repo_root, path):
    try:
        raw_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    code_lines = _strip_comments(raw_lines)
    relative = path.resolve().relative_to(repo_root.resolve()).as_posix()
    declaration = next((value for line in code_lines if (value := _class_declaration(line))), None)
    if not declaration:
        return None

    brace = 0
    pending = []
    current_class = None
    class_depth = None
    class_tx = {"present": False, "read_only": False, "line": None, "text": ""}
    methods = []
    current_method = None
    for index, code in enumerate(code_lines):
        line_no = index + 1
        stripped = code.strip()
        if stripped.startswith("@"):
            pending.append({"line": line_no, "text": stripped})
        class_decl = _class_declaration(code)
        if class_decl:
            current_class = class_decl
            class_depth = brace + code.count("{") - code.count("}")
            class_tx = _transaction_annotation(pending)
            pending = []
        name = _method_name(code)
        if name and current_class:
            method_tx = _transaction_annotation(pending)
            effective_tx = method_tx if method_tx["present"] else class_tx
            current_method = {
                "name": name,
                "class_name": current_class["name"],
                "file": relative,
                "start_line": line_no,
                "end_line": line_no,
                "depth": brace + code.count("{") - code.count("}"),
                "transaction": effective_tx,
                "transaction_scope": "method" if method_tx["present"] else ("class" if class_tx["present"] else "none"),
            }
            methods.append(current_method)
            pending = []
        elif stripped and not stripped.startswith("@") and not class_decl and current_method is None:
            pending = []
        brace += code.count("{") - code.count("}")
        if current_method:
            current_method["end_line"] = line_no
            if brace < current_method["depth"]:
                current_method = None
        if current_class and class_depth is not None and brace < class_depth:
            current_class = None
            class_depth = None
            class_tx = {"present": False, "read_only": False, "line": None, "text": ""}

    receivers = _field_receivers(code_lines, declaration["name"])
    calls = []
    methods_pattern = "|".join(sorted(WRITE_METHODS, key=lambda x: (-len(x), x)))
    call_re = re.compile(
        rf"(?:\bthis\s*\.\s*)?\b([A-Za-z_$][A-Za-z0-9_$]*)\s*\.\s*({methods_pattern})\s*\("
    )
    for method in methods:
        for line_no in range(method["start_line"], method["end_line"] + 1):
            code = code_lines[line_no - 1]
            for match in call_re.finditer(code):
                receiver = match.group(1)
                receiver_type = receivers.get(receiver)
                if not receiver_type:
                    continue
                calls.append({
                    "file": relative,
                    "line": line_no,
                    "snippet": raw_lines[line_no - 1].strip()[:500],
                    "caller_type": declaration["name"],
                    "caller_method": method["name"],
                    "receiver": receiver,
                    "receiver_type": receiver_type,
                    "operation": match.group(2),
                    "transaction": method["transaction"],
                    "transaction_scope": method["transaction_scope"],
                })
    return {
        "file": relative,
        "class_name": declaration["name"],
        "parents": declaration["parents"],
        "receivers": receivers,
        "methods": methods,
        "calls": calls,
        "raw_lines": raw_lines,
    }


def _iter_java_files(repo_root):
    for path in sorted(repo_root.rglob("*.java"), key=lambda x: x.as_posix()):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        yield path


def _method_at(parsed, line):
    matches = [m for m in parsed.get("methods") or [] if int(m["start_line"]) <= line <= int(m["end_line"])]
    return min(matches, key=lambda x: int(x["end_line"]) - int(x["start_line"])) if matches else None


def _event_evidence(run_dir, node, repo_root):
    for evidence_id in node.get("evidence") or []:
        evidence = _read_json(Path(run_dir) / "evidence" / f"{evidence_id}.json", {})
        ref = canonicalize_evidence_ref(evidence, repo_root=str(repo_root), allow_repo_absolute=True)
        if ref is not None:
            ref["source_type"] = "event"
            ref["event_id"] = str(node.get("event_id") or "")
            return ref
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    scope = meta.get("scope") if isinstance(meta.get("scope"), dict) else {}
    return canonicalize_evidence_ref({
        "source_type": "event", "event_id": str(node.get("event_id") or ""),
        "file": meta.get("path"), "start_line": scope.get("start_line"), "end_line": scope.get("end_line"),
    }, repo_root=str(repo_root), allow_repo_absolute=True)


def _type_aliases(repository_type):
    aliases = {repository_type}
    if repository_type.endswith("Override"):
        aliases.add(repository_type[:-len("Override")])
    return aliases


def _coverage(calls):
    if not calls:
        return "unknown", 0.52, ["direct_callsite_not_observed"]
    statuses = []
    for call in calls:
        tx = call.get("transaction") or {}
        if not tx.get("present"):
            statuses.append("uncovered")
        elif tx.get("read_only"):
            statuses.append("read_only_transaction")
        else:
            statuses.append("covered_explicit")
    unique = set(statuses)
    if unique == {"covered_explicit"}:
        return "covered_explicit", 0.94, []
    if unique == {"uncovered"}:
        return "uncovered", 0.91, []
    if unique == {"read_only_transaction"}:
        return "read_only_transaction", 0.9, ["write_call_inside_read_only_transaction"]
    limitations = ["partial_transaction_coverage"]
    if "read_only_transaction" in unique:
        limitations.append("write_call_inside_read_only_transaction")
    return "partially_covered", 0.74, limitations


def correlate_spring_transactions(run_dir, repo_path):
    repo_root = Path(repo_path).expanduser().resolve()
    graph = _read_json(Path(run_dir) / "event_graph.json", {"nodes": []})
    parsed_files = {}
    calls_by_target = defaultdict(list)
    for path in _iter_java_files(repo_root):
        parsed = _parse_java_file(repo_root, path)
        if not parsed:
            continue
        parsed_files[parsed["file"]] = parsed
        for call in parsed["calls"]:
            calls_by_target[(call["receiver_type"], call["operation"])].append(call)

    db_nodes = []
    for node in graph.get("nodes") or []:
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        if str(node.get("type") or "") == "db_op" and str(meta.get("language") or "") == "java" and str(meta.get("db.kind") or "") == "db.write":
            db_nodes.append(node)

    correlations = []
    call_pattern = re.compile(r"(?:\bthis\s*\.\s*)?\b([A-Za-z_$][A-Za-z0-9_$]*)\s*\.\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*\(")
    for node in db_nodes:
        meta = node.get("meta") or {}
        db_ref = _event_evidence(run_dir, node, repo_root)
        if db_ref is None:
            continue
        parsed = parsed_files.get(db_ref["file"])
        method = _method_at(parsed, db_ref["start_line"]) if parsed else None
        source_line = parsed["raw_lines"][db_ref["start_line"] - 1] if parsed and db_ref["start_line"] <= len(parsed["raw_lines"]) else ""
        match = call_pattern.search(source_line)
        receiver = str(meta.get("repo_symbol") or (match.group(1) if match else ""))
        direct_operation = match.group(2) if match else ""
        interfaces = [x for x in ((parsed or {}).get("parents") or []) if _is_receiver_type(x)]
        repository_type = ""
        operation = direct_operation or str(meta.get("db.op") or "")
        if interfaces and method:
            repository_type = interfaces[0]
            operation = method["name"]
        elif parsed and receiver in parsed.get("receivers", {}):
            repository_type = parsed["receivers"][receiver]
        elif parsed and _is_receiver_type(parsed.get("class_name")):
            repository_type = parsed["class_name"]
            operation = method["name"] if method else operation

        calls = []
        for alias in _type_aliases(repository_type) if repository_type else []:
            calls.extend(calls_by_target.get((alias, operation), []))
        calls = sorted({(c["file"], c["line"], c["caller_method"]): c for c in calls}.values(), key=lambda x: (x["file"], x["line"], x["caller_method"]))
        coverage_status, confidence, limitations = _coverage(calls)
        if not repository_type or not operation:
            coverage_status, confidence = "unknown", 0.45
            limitations = sorted(set(limitations + ["repository_target_unresolved"]))

        call_refs, tx_refs, callsite_rows = [], [], []
        for call in calls:
            call_ref = canonicalize_evidence_ref({
                "source_type": "transaction_callsite", "file": call["file"],
                "start_line": call["line"], "end_line": call["line"], "snippet": call["snippet"],
            })
            if call_ref is not None:
                call_refs.append(call_ref)
            tx = call.get("transaction") or {}
            if tx.get("present") and isinstance(tx.get("line"), int) and tx["line"] >= 1:
                tx_ref = canonicalize_evidence_ref({
                    "source_type": "transaction_annotation", "file": call["file"],
                    "start_line": tx["line"], "end_line": tx["line"], "snippet": tx.get("text") or "@Transactional",
                })
                if tx_ref is not None:
                    tx_refs.append(tx_ref)
            callsite_rows.append({
                "file": call["file"], "line": call["line"], "caller_type": call["caller_type"],
                "caller_method": call["caller_method"], "receiver": call["receiver"],
                "receiver_type": call["receiver_type"], "transaction_scope": call["transaction_scope"],
                "read_only": bool(tx.get("read_only")),
            })

        primary = calls[0] if calls else {}
        correlation = {
            "db_event_id": str(node.get("event_id") or ""), "coverage_status": coverage_status,
            "confidence": confidence, "caller_file": primary.get("file") or "",
            "caller_type": primary.get("caller_type") or "", "caller_method": primary.get("caller_method") or "",
            "callsite_line": primary.get("line") if primary else None,
            "repository_receiver": primary.get("receiver") or receiver, "repository_type": repository_type,
            "operation": operation, "transaction_scope": primary.get("transaction_scope") or "none",
            "transaction_evidence_refs": tx_refs, "callsite_evidence_refs": call_refs,
            "db_write_evidence_refs": [db_ref], "db_write_file": db_ref["file"],
            "db_write_line": db_ref["start_line"], "callsites": callsite_rows, "limitations": limitations,
        }
        correlation["correlation_id"] = make_correlation_id(correlation["db_event_id"], repository_type, operation, callsite_rows)
        correlations.append(correlation)

    correlations = stable_sort_correlations(correlations)
    counts = Counter(item["coverage_status"] for item in correlations)
    unique_calls = {
        (str(call.get("file") or ""), int(call.get("line") or 0), str(call.get("caller_method") or "")): call
        for item in correlations
        for call in (item.get("callsites") or [])
    }
    summary_limitations = [
        "Direct Java callsites and explicit Spring @Transactional annotations only.",
        "Does not model Spring proxy behavior, self-invocation, reflection, custom AOP, or cross-service transactions.",
        "A covered direct call does not prove every runtime entrypoint is transactional.",
    ]
    if len(correlations) < len(db_nodes):
        summary_limitations.append(
            f"{len(db_nodes) - len(correlations)} DB write event(s) had no valid source location and were not assigned a correlation."
        )
    summary = {
        "version": "transaction_correlation_summary_v1", "total_correlations": len(correlations),
        "db_writes_considered": len(db_nodes),
        "counts_by_coverage_status": {key: int(counts.get(key, 0)) for key in ["covered_explicit", "uncovered", "partially_covered", "read_only_transaction", "unknown"]},
        "explicit_covered_call_count": sum(1 for call in unique_calls.values() if call.get("transaction_scope") in ("method", "class") and not call.get("read_only")),
        "uncovered_call_count": sum(1 for call in unique_calls.values() if call.get("transaction_scope") == "none"),
        "read_only_write_call_count": sum(1 for call in unique_calls.values() if call.get("read_only")),
        "limitations": summary_limitations,
    }
    return {
        "version": "transaction_correlations_v1", "language": "java", "framework": "spring",
        "correlations": correlations, "limitations": summary["limitations"],
    }, summary
