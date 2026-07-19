from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from ...evidence.location import canonicalize_evidence_ref
from .correlation_schema import make_correlation_id, stable_sort_correlations


TRUSTED_DECORATOR_MODULES = {
    "typeorm-transactional",
    "typeorm-transactional-cls-hooked",
    "typeorm",
}
TRUSTED_DECORATOR_SYMBOLS = {"Transactional", "Transaction"}
IGNORED_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "build",
    "dist",
    "coverage",
    "out",
    "__pycache__",
}


def _read_json(path, default):
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return default


def _source_ref(file_name, line, snippet, source_type):
    return canonicalize_evidence_ref(
        {
            "source_type": source_type,
            "file": file_name,
            "start_line": line,
            "end_line": line,
            "snippet": str(snippet or "").strip()[:500],
        }
    )


def _iter_typescript_files(repo_root):
    for path in sorted(repo_root.rglob("*"), key=lambda value: value.as_posix()):
        if not path.is_file() or path.suffix.lower() not in {".ts", ".tsx"}:
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        yield path


def _imports(text):
    values = {}
    pattern = re.compile(
        r"import\s*\{(?P<body>[^}]+)\}\s*from\s*['\"](?P<module>[^'\"]+)['\"]",
        re.MULTILINE | re.DOTALL,
    )
    for match in pattern.finditer(text):
        for raw in match.group("body").split(","):
            bits = re.split(r"\s+as\s+", raw.strip())
            original = bits[0].strip()
            local = bits[-1].strip()
            if original and local:
                values[local] = {
                    "original": original,
                    "module": match.group("module"),
                }
    return values


def _brace_end(lines, start):
    depth = 0
    opened = False
    for index in range(start, len(lines)):
        line = lines[index]
        if "{" in line:
            opened = True
        depth += line.count("{") - line.count("}")
        if opened and depth <= 0:
            return index + 1
    return len(lines)


def _decorators_above(lines, index):
    rows = []
    cursor = index - 1
    while cursor >= 0:
        stripped = lines[cursor].strip()
        if not stripped:
            if rows:
                break
            cursor -= 1
            continue
        if stripped.startswith("@") or (rows and not stripped.endswith(")")):
            rows.append((cursor + 1, stripped))
            cursor -= 1
            continue
        break
    rows.reverse()
    out = []
    for line, text in rows:
        match = re.match(r"@([A-Za-z_$][A-Za-z0-9_$.]*)", text)
        if match:
            out.append({"name": match.group(1).split(".")[-1], "line": line, "text": text})
    return out


def _class_ranges(lines):
    values = []
    for index, line in enumerate(lines):
        match = re.search(r"\bclass\s+([A-Za-z_$][A-Za-z0-9_$]*)[^{]*\{", line)
        if not match:
            continue
        values.append(
            {
                "name": match.group(1),
                "start": index + 1,
                "end": _brace_end(lines, index),
                "decorators": _decorators_above(lines, index),
            }
        )
    return values


def _method_ranges(lines, classes):
    values = []
    method_re = re.compile(
        r"^\s*(?:(?:public|private|protected|static|async|readonly|override|abstract)\s+)*"
        r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*(?:<[^>{}]+>)?\s*\([^;{}]*\)"
        r"\s*(?::[^={]+)?\s*\{"
    )
    for index, line in enumerate(lines):
        if not line.strip() or line.lstrip().startswith("@"):
            continue
        statement_lines = []
        for candidate in lines[index : min(len(lines), index + 10)]:
            statement_lines.append(candidate)
            if "{" in candidate or ";" in candidate:
                break
        statement = "\n".join(statement_lines)
        match = method_re.search(statement)
        if not match or match.group("name") in {"if", "for", "while", "switch", "catch"}:
            continue
        line_no = index + 1
        owner = next(
            (
                item
                for item in classes
                if item["start"] <= line_no <= item["end"]
            ),
            None,
        )
        if owner is None:
            continue
        values.append(
            {
                "name": match.group("name"),
                "class_name": owner["name"],
                "class_decorators": owner["decorators"],
                "start": line_no,
                "end": _brace_end(lines, index),
                "decorators": _decorators_above(lines, index),
            }
        )
    return values


def _field_types(lines, classes):
    values = defaultdict(dict)
    typed = re.compile(
        r"(?:private|protected|public)?\s*(?:readonly\s+)?"
        r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*[!?]?\s*:\s*"
        r"(?P<type>[A-Za-z_$][A-Za-z0-9_$.]*)"
    )
    for owner in classes:
        body = "\n".join(lines[owner["start"] - 1 : owner["end"]])
        for match in typed.finditer(body):
            values[owner["name"]][match.group("name")] = match.group("type").split(".")[-1]
    return values


def _decorator_state(decorators, imports, custom_trusted):
    untrusted = False
    for decorator in reversed(decorators or []):
        name = decorator["name"]
        info = imports.get(name)
        trusted = bool(
            info
            and info["original"] in TRUSTED_DECORATOR_SYMBOLS
            and info["module"] in TRUSTED_DECORATOR_MODULES
        )
        if name in custom_trusted:
            trusted = True
        if not trusted and (
            name in TRUSTED_DECORATOR_SYMBOLS
            or "transaction" in name.lower()
        ):
            untrusted = True
            continue
        if trusted:
            text = decorator["text"]
            return {
                "trusted": True,
                "untrusted": False,
                "read_only": bool(
                    re.search(
                        r"readOnly\s*(?:=|:)\s*true",
                        text,
                        flags=re.IGNORECASE,
                    )
                ),
                "line": decorator["line"],
                "text": text,
            }
    return {
        "trusted": False,
        "untrusted": untrusted,
        "read_only": False,
        "line": None,
        "text": "",
    }


def _custom_trusted_names(files):
    names = set()
    for parsed in files.values():
        trusted_locals = {
            local
            for local, info in parsed["imports"].items()
            if info["original"] in TRUSTED_DECORATOR_SYMBOLS
            and info["module"] in TRUSTED_DECORATOR_MODULES
        }
        if not trusted_locals:
            continue
        trusted_call = "|".join(re.escape(value) for value in sorted(trusted_locals))
        definition = re.compile(
            r"^\s*(?:export\s+)?(?:function|const)\s+"
            r"([A-Za-z_$][A-Za-z0-9_$]*)",
        )
        for index, line in enumerate(parsed["lines"]):
            match = definition.search(line)
            if not match:
                continue
            end = (
                _brace_end(parsed["lines"], index)
                if "{" in line
                else index + 1
            )
            body = "\n".join(parsed["lines"][index:end])
            if re.search(r"\b(?:" + trusted_call + r")\s*\(", body):
                names.add(match.group(1))
    return names


def _parse_files(repo_root):
    parsed = {}
    for path in _iter_typescript_files(repo_root):
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError):
            continue
        lines = text.splitlines()
        relative = path.resolve().relative_to(repo_root.resolve()).as_posix()
        classes = _class_ranges(lines)
        parsed[relative] = {
            "file": relative,
            "text": text,
            "lines": lines,
            "imports": _imports(text),
            "classes": classes,
            "methods": _method_ranges(lines, classes),
            "field_types": _field_types(lines, classes),
        }
    custom_trusted = _custom_trusted_names(parsed)
    for item in parsed.values():
        item["custom_trusted"] = custom_trusted
    return parsed


def _method_at(parsed, line):
    matches = [
        item
        for item in (parsed or {}).get("methods", [])
        if item["start"] <= line <= item["end"]
    ]
    return min(matches, key=lambda item: item["end"] - item["start"]) if matches else None


def _class_at(parsed, line):
    matches = [
        item
        for item in (parsed or {}).get("classes", [])
        if item["start"] <= line <= item["end"]
    ]
    return min(matches, key=lambda item: item["end"] - item["start"]) if matches else None


def _method_transaction(parsed, method):
    if not method:
        return {"trusted": False, "untrusted": False, "read_only": False}
    method_state = _decorator_state(
        method["decorators"], parsed["imports"], parsed["custom_trusted"]
    )
    if method_state["trusted"] or method_state["untrusted"]:
        method_state["scope"] = "method"
        return method_state
    class_state = _decorator_state(
        method["class_decorators"],
        parsed["imports"],
        parsed["custom_trusted"],
    )
    class_state["scope"] = "class"
    return class_state


def _direct_calls(parsed_files):
    calls = defaultdict(list)
    for parsed in parsed_files.values():
        for method in parsed["methods"]:
            field_types = parsed["field_types"].get(method["class_name"], {})
            tx = _method_transaction(parsed, method)
            for line_no in range(method["start"], method["end"] + 1):
                line = parsed["lines"][line_no - 1]
                for match in re.finditer(
                    r"\bthis\.([A-Za-z_$][A-Za-z0-9_$]*)"
                    r"\.([A-Za-z_$][A-Za-z0-9_$]*)\s*\(",
                    line,
                ):
                    receiver, target_method = match.groups()
                    target_class = field_types.get(receiver)
                    if not target_class:
                        continue
                    calls[(target_class, target_method)].append(
                        {
                            "file": parsed["file"],
                            "line": line_no,
                            "snippet": line.strip(),
                            "caller_class": method["class_name"],
                            "caller_method": method["name"],
                            "receiver": receiver,
                            "target_class": target_class,
                            "target_method": target_method,
                            "transaction": tx,
                        }
                    )
    return calls


def _nearest_transaction_ref(parsed, method, operation_line):
    if not parsed:
        return None, "typeorm_callback"
    best = None
    start_line = method["start"] if method else max(1, operation_line - 200)
    for line_no in range(start_line, operation_line + 1):
        line = parsed["lines"][line_no - 1]
        match = re.search(
            r"(?P<receiver>(?:this\.)?[A-Za-z_$][A-Za-z0-9_$]*)"
            r"\.transaction\s*\(",
            line,
        )
        if (
            match
            and _brace_end(parsed["lines"], line_no - 1) >= operation_line
        ):
            best = (line_no, line, match.group("receiver").removeprefix("this."))
    if best is None:
        return None, "typeorm_callback"
    owner = method or _class_at(parsed, operation_line) or {}
    field_types = parsed["field_types"].get(owner.get("class_name") or owner.get("name"), {})
    receiver_type = field_types.get(best[2], "")
    mechanism = (
        "entity_manager_callback"
        if receiver_type == "EntityManager"
        else "typeorm_callback"
    )
    return _source_ref(parsed["file"], best[0], best[1], "transaction_boundary"), mechanism


def _query_runner_ref(parsed, method, operation_line, receiver_name):
    if not parsed or not method:
        return None
    base = str(receiver_name or "").replace("this.", "").split(".", 1)[0]
    best = None
    for line_no in range(method["start"], operation_line + 1):
        line = parsed["lines"][line_no - 1]
        if re.search(
            rf"(?:this\.)?{re.escape(base)}\.startTransaction\s*\(",
            line,
        ):
            best = (line_no, line)
    if best is None:
        return None
    return _source_ref(parsed["file"], best[0], best[1], "transaction_boundary")


def _event_map(run_root, repo_root):
    graph = _read_json(run_root / "event_graph.json", {"nodes": []})
    values = {}
    for node in graph.get("nodes") or []:
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        if str(meta.get("framework") or "").lower() != "typeorm":
            continue
        if str(meta.get("db.kind") or "") != "db.write":
            continue
        for evidence_id in node.get("evidence") or []:
            raw = _read_json(run_root / "evidence" / f"{evidence_id}.json", {})
            ref = canonicalize_evidence_ref(
                raw,
                repo_root=str(repo_root),
                allow_repo_absolute=True,
            )
            if ref is None:
                continue
            key = (
                ref["file"],
                ref["start_line"],
                str(meta.get("db.op") or ""),
            )
            values.setdefault(key, str(node.get("event_id") or ""))
    return values


def _call_refs(calls):
    refs = []
    for call in calls:
        ref = _source_ref(
            call["file"],
            call["line"],
            call["snippet"],
            "transaction_callsite",
        )
        if ref is not None:
            refs.append(ref)
    return refs


def _transaction_refs(calls, parsed_files):
    refs = []
    for call in calls:
        tx = call.get("transaction") or {}
        if not tx.get("trusted") or not isinstance(tx.get("line"), int):
            continue
        parsed = parsed_files.get(call["file"])
        snippet = (
            parsed["lines"][tx["line"] - 1]
            if parsed and tx["line"] <= len(parsed["lines"])
            else tx.get("text")
        )
        ref = _source_ref(
            call["file"],
            tx["line"],
            snippet,
            "transaction_decorator",
        )
        if ref is not None:
            refs.append(ref)
    return refs


def _wrapper_coverage(calls):
    if not calls:
        return None
    states = []
    for call in calls:
        tx = call.get("transaction") or {}
        if tx.get("trusted") and tx.get("read_only"):
            states.append("read_only_transaction")
        elif tx.get("trusted"):
            states.append("covered_explicit")
        elif tx.get("untrusted"):
            states.append("unknown")
        else:
            states.append("uncovered")
    unique = set(states)
    if unique == {"covered_explicit"}:
        return "covered_explicit", 0.9, []
    if unique == {"uncovered"}:
        return "uncovered", 0.84, []
    if unique == {"read_only_transaction"}:
        return (
            "read_only_transaction",
            0.86,
            ["write_call_inside_read_only_transaction"],
        )
    limitations = ["partial_transaction_coverage"]
    if "unknown" in unique:
        limitations.append("direct_caller_target_unresolved")
    if "read_only_transaction" in unique:
        limitations.append("write_call_inside_read_only_transaction")
    return "partially_covered", 0.72, limitations


def correlate_typescript_transactions(run_dir, repo_path):
    run_root = Path(run_dir)
    repo_root = Path(repo_path).expanduser().resolve()
    artifact = _read_json(run_root / "typeorm_db_operations.json", {})
    operations = [
        item
        for item in artifact.get("operations") or []
        if isinstance(item, dict) and item.get("kind") == "db.write"
    ]
    parsed_files = _parse_files(repo_root)
    direct_calls = _direct_calls(parsed_files)
    method_definitions = Counter(
        (method["class_name"], method["name"])
        for parsed in parsed_files.values()
        for method in parsed["methods"]
    )
    event_ids = _event_map(run_root, repo_root)
    correlations = []

    for operation in operations:
        file_name = str(operation.get("file") or "")
        line = int(operation.get("line_start") or 0)
        parsed = parsed_files.get(file_name)
        method = _method_at(parsed, line)
        db_refs = [
            ref
            for ref in (operation.get("evidence_refs") or [])
            if canonicalize_evidence_ref(ref) is not None
        ]
        if not db_refs:
            continue
        event_id = event_ids.get(
            (file_name, line, str(operation.get("operation") or "")),
            "",
        )
        target_class = method["class_name"] if method else ""
        target_method = method["name"] if method else ""
        coverage_status = "unknown"
        mechanism = "unknown"
        confidence = 0.55
        limitations = []
        callsite_refs = list(db_refs)
        transaction_refs = []
        calls = []
        caller = {}
        tx_context = str(operation.get("transaction_context") or "unknown")

        if tx_context == "explicit_callback":
            tx_ref, mechanism = _nearest_transaction_ref(parsed, method, line)
            if tx_ref is not None:
                coverage_status = "covered_explicit"
                confidence = 0.96
                transaction_refs = [tx_ref]
            else:
                limitations.append("transaction_callback_boundary_unresolved")
        elif tx_context == "query_runner_explicit":
            tx_ref = _query_runner_ref(
                parsed, method, line, operation.get("receiver_name")
            )
            mechanism = "query_runner"
            if tx_ref is not None:
                coverage_status = "covered_explicit"
                confidence = 0.96
                transaction_refs = [tx_ref]
            else:
                limitations.append("query_runner_scope_unresolved")
        else:
            tx = _method_transaction(parsed, method)
            if tx.get("trusted"):
                mechanism = (
                    "trusted_decorator_method"
                    if tx.get("scope") == "method"
                    else "trusted_decorator_class"
                )
                coverage_status = (
                    "read_only_transaction"
                    if tx.get("read_only")
                    else "covered_explicit"
                )
                confidence = 0.93
                if tx.get("read_only"):
                    limitations.append("write_call_inside_read_only_transaction")
                snippet = parsed["lines"][tx["line"] - 1]
                tx_ref = _source_ref(
                    file_name,
                    tx["line"],
                    snippet,
                    "transaction_decorator",
                )
                if tx_ref is not None:
                    transaction_refs = [tx_ref]
            else:
                target_key = (target_class, target_method)
                wrapper_calls = (
                    direct_calls.get(target_key, [])
                    if method_definitions.get(target_key, 0) == 1
                    else []
                )
                wrapper_result = _wrapper_coverage(wrapper_calls)
                if wrapper_result:
                    coverage_status, confidence, limitations = wrapper_result
                    mechanism = "direct_wrapper_caller"
                    calls = wrapper_calls
                    caller = wrapper_calls[0]
                    callsite_refs = _call_refs(wrapper_calls)
                    transaction_refs = _transaction_refs(
                        wrapper_calls, parsed_files
                    )
                elif tx.get("untrusted"):
                    limitations.append(
                        "transaction_decorator_provenance_unresolved"
                    )
                elif any(
                    part.lower() in {"migration", "migrations"}
                    for part in Path(file_name).parts
                ):
                    limitations.append(
                        "migration_transaction_policy_requires_confirmation"
                    )
                elif method_definitions.get(target_key, 0) > 1:
                    limitations.append("direct_caller_target_unresolved")
                elif method and not re.search(
                    r"(?:Repository|Repo|Dao)$", target_class
                ):
                    coverage_status = "uncovered"
                    mechanism = "none"
                    confidence = 0.8
                else:
                    limitations.append("transaction_coverage_unresolved")

        if coverage_status == "unknown" and not limitations:
            limitations.append("transaction_coverage_unresolved")
        callsite_rows = [
            {
                "file": call["file"],
                "line": call["line"],
                "caller_type": call["caller_class"],
                "caller_method": call["caller_method"],
                "receiver": call["receiver"],
                "receiver_type": call["target_class"],
                "transaction_scope": (
                    (call.get("transaction") or {}).get("scope") or "none"
                ),
                "read_only": bool(
                    (call.get("transaction") or {}).get("read_only")
                ),
            }
            for call in calls
        ]
        correlation = {
            "db_event_id": event_id or str(operation.get("operation_id") or ""),
            "db_operation_id": str(operation.get("operation_id") or ""),
            "language": "typescript",
            "framework": "typeorm",
            "coverage_status": coverage_status,
            "transaction_mechanism": mechanism,
            "confidence": confidence,
            "caller_file": caller.get("file") or file_name,
            "caller_type": caller.get("caller_class") or target_class,
            "caller_class": caller.get("caller_class") or target_class,
            "caller_method": caller.get("caller_method") or target_method,
            "callsite_line": caller.get("line") or line,
            "target_file": file_name,
            "target_class": target_class,
            "target_method": target_method,
            "repository_receiver": str(operation.get("receiver_name") or ""),
            "repository_type": target_class,
            "receiver_kind": str(operation.get("receiver_kind") or "unknown"),
            "receiver_name": str(operation.get("receiver_name") or ""),
            "operation": str(operation.get("operation") or ""),
            "transaction_scope": mechanism,
            "transaction_evidence_refs": transaction_refs,
            "callsite_evidence_refs": callsite_refs,
            "db_write_evidence_refs": db_refs,
            "db_write_file": file_name,
            "db_write_line": line,
            "callsites": callsite_rows,
            "limitations": sorted(set(limitations)),
        }
        correlation["correlation_id"] = make_correlation_id(
            correlation["db_event_id"],
            correlation["repository_type"],
            correlation["operation"],
            callsite_rows
            or [
                {
                    "file": correlation["caller_file"],
                    "line": correlation["callsite_line"],
                    "caller_method": correlation["caller_method"],
                }
            ],
        )
        correlations.append(correlation)

    correlations = stable_sort_correlations(correlations)
    coverage = Counter(item["coverage_status"] for item in correlations)
    mechanisms = Counter(item["transaction_mechanism"] for item in correlations)
    summary = {
        "version": "transaction_correlation_summary_v1",
        "language": "typescript",
        "framework": "typeorm",
        "total_correlations": len(correlations),
        "db_writes_considered": len(operations),
        "counts_by_coverage_status": {
            key: int(coverage.get(key, 0))
            for key in [
                "covered_explicit",
                "uncovered",
                "partially_covered",
                "read_only_transaction",
                "unknown",
            ]
        },
        "counts_by_transaction_mechanism": dict(sorted(mechanisms.items())),
        "migration_unresolved_write_count": sum(
            "migration_transaction_policy_requires_confirmation"
            in (item.get("limitations") or [])
            for item in correlations
        ),
        "limitations": [
            "TypeScript correlation is limited to explicit local scopes and one-hop statically resolved wrapper calls.",
            "It does not model runtime dependency injection, reflection, or multi-hop call graphs.",
            "Explicit transaction coverage does not prove rollback behavior or every runtime entrypoint.",
        ],
    }
    return {
        "version": "transaction_correlations_v1",
        "language": "typescript",
        "framework": "typeorm",
        "correlations": correlations,
        "limitations": list(summary["limitations"]),
    }, summary
