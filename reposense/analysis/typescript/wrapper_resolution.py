from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from .import_graph import resolve_type, source_ref
from .import_graph_schema import stable_sort_resolutions


TYPEORM_RECEIVER_TYPES = {
    "Repository",
    "TreeRepository",
    "MongoRepository",
    "EntityManager",
    "DataSource",
    "QueryRunner",
}
WRAPPER_NAME = re.compile(r"(?:Repository|Repo|Dao)$")


def _method_for_line(parsed, class_name, line):
    matches = [
        item
        for item in parsed.get("methods") or []
        if item["class_name"] == class_name
        and item["start"] <= line <= item["end"]
    ]
    return min(
        matches, key=lambda item: item["end"] - item["start"]
    ) if matches else None


def _dependency_map(parsed, class_name):
    values = {}
    for row in (
        list(parsed["constructor_dependencies"].get(class_name, []))
        + list(parsed["properties"].get(class_name, []))
    ):
        values.setdefault(row["name"], row)
    return values


def _operation_methods(index, operations):
    values = defaultdict(list)
    for operation in operations:
        file_name = str(operation.get("file") or "")
        parsed = index["files"].get(file_name)
        if not parsed:
            continue
        line = int(operation.get("line_start") or 0)
        owner = next(
            (
                item
                for item in parsed["classes"]
                if item["kind"] == "class"
                and item["start"] <= line <= item["end"]
            ),
            None,
        )
        if owner is None:
            continue
        method = _method_for_line(parsed, owner["name"], line)
        if method is None:
            continue
        values[(file_name, owner["name"], method["name"])].append(operation)
    return values


def _symbol_lookup(index, name):
    return [
        item
        for item in index["symbols"]
        if item["name"] == name and item["kind"] == "class"
    ]


def _provider_targets(index, symbol):
    provider_rows = [
        item
        for item in index["providers"]
        if item["provide"] == symbol["name"]
    ]
    targets = []
    for provider in provider_rows:
        resolved, _, _ = resolve_type(
            index, provider["file"], provider["use_class"]
        )
        if not resolved:
            resolved = [
                {"symbol": item, "depth": 0, "path": [item["file"]]}
                for item in _symbol_lookup(index, provider["use_class"])
            ]
        for item in resolved:
            targets.append(
                {
                    **item,
                    "provider_evidence_refs": provider.get(
                        "evidence_refs", []
                    ),
                }
            )
    unique = {}
    for item in targets:
        target = item["symbol"]
        unique[(target["file"], target["name"])] = item
    return list(unique.values())


def _candidate_targets(index, source_file, declared_type):
    resolved, imported, limitations = resolve_type(
        index, source_file, declared_type
    )
    expanded = []
    for item in resolved:
        symbol = item["symbol"]
        if symbol["kind"] == "interface" or symbol.get("abstract"):
            providers = _provider_targets(index, symbol)
            if providers:
                expanded.extend(providers)
            else:
                limitations.append("dynamic_di_token_unresolved")
        else:
            expanded.append(item)
    unique = {}
    for item in expanded:
        symbol = item["symbol"]
        unique[(symbol["file"], symbol["name"])] = item
    return list(unique.values()), imported, sorted(set(limitations))


def _resolution_status(imported, target, local_assignment):
    if local_assignment:
        return "resolved_local_assignment"
    if target.get("depth", 0) > 0:
        path = target.get("path") or []
        if any(Path(item).name.startswith("index.") for item in path):
            return "resolved_barrel"
        return "resolved_reexport"
    if imported and imported.get("kind") == "named" and (
        imported.get("local") != imported.get("imported")
    ):
        return "resolved_alias_import"
    return "resolved_direct_import"


def _method_calls(parsed, method):
    local_aliases = {}
    for line_no in range(method["start"], method["end"] + 1):
        line = parsed["lines"][line_no - 1]
        assignment = re.search(
            r"\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*="
            r"\s*this\.([A-Za-z_$][A-Za-z0-9_$]*)\s*;?",
            line,
        )
        if assignment:
            local_aliases[assignment.group(1)] = assignment.group(2)
        for match in re.finditer(
            r"\bthis\.([A-Za-z_$][A-Za-z0-9_$]*)"
            r"\.([A-Za-z_$][A-Za-z0-9_$]*)\s*\(",
            line,
        ):
            yield {
                "receiver": match.group(1),
                "target_method": match.group(2),
                "line": line_no,
                "snippet": line.strip(),
                "local_assignment": False,
            }
        for match in re.finditer(
            r"(?<![\w$.])([A-Za-z_$][A-Za-z0-9_$]*)"
            r"\.([A-Za-z_$][A-Za-z0-9_$]*)\s*\(",
            line,
        ):
            alias = match.group(1)
            if alias not in local_aliases:
                continue
            yield {
                "receiver": local_aliases[alias],
                "target_method": match.group(2),
                "line": line_no,
                "snippet": line.strip(),
                "local_assignment": True,
            }


def _is_test_file(file_name):
    lowered = file_name.lower()
    return (
        lowered.endswith((".spec.ts", ".test.ts", ".spec.tsx", ".test.tsx"))
        or any(
            part in {"test", "tests", "__tests__", "fixtures"}
            for part in Path(lowered).parts
        )
    )


def resolve_typeorm_wrappers(index, operations):
    operation_methods = _operation_methods(index, operations)
    rows = []
    for source_file in sorted(index["files"]):
        if _is_test_file(source_file):
            continue
        parsed = index["files"][source_file]
        for method in parsed["methods"]:
            dependencies = _dependency_map(parsed, method["class_name"])
            for call in _method_calls(parsed, method):
                dependency = dependencies.get(call["receiver"])
                if not dependency:
                    continue
                declared_type = str(dependency.get("declared_type") or "")
                base_type = declared_type.split(".")[-1]
                if base_type in TYPEORM_RECEIVER_TYPES:
                    continue
                targets, imported, limitations = _candidate_targets(
                    index, source_file, declared_type
                )
                dynamic_token = str(
                    dependency.get("dynamic_inject_token") or ""
                )
                if dynamic_token and dynamic_token not in {
                    declared_type,
                    base_type,
                }:
                    targets = []
                    limitations.append("dynamic_di_token_unresolved")
                matching = []
                for target in targets:
                    symbol = target["symbol"]
                    key = (
                        symbol["file"],
                        symbol["name"],
                        call["target_method"],
                    )
                    if operation_methods.get(key):
                        matching.append(target)
                if not matching and not WRAPPER_NAME.search(base_type):
                    continue
                status = "unresolved"
                target = None
                if len(matching) == 1:
                    target = matching[0]
                    status = _resolution_status(
                        imported, target, call["local_assignment"]
                    )
                elif len(matching) > 1 or len(targets) > 1:
                    status = "ambiguous"
                    limitations.append("target_method_ambiguous")
                elif targets:
                    target = targets[0]
                    limitations.append(
                        "target_method_without_canonical_db_operation"
                    )
                elif not limitations:
                    limitations.append("receiver_type_unresolved")
                target_symbol = target["symbol"] if target else {}
                target_key = (
                    target_symbol.get("file", ""),
                    target_symbol.get("name", ""),
                    call["target_method"],
                )
                db_operations = operation_methods.get(target_key, [])
                import_refs = list(
                    (imported or {}).get("evidence_refs") or []
                )
                if target:
                    import_refs.extend(
                        target.get("reexport_evidence_refs") or []
                    )
                    import_refs.extend(
                        target.get("provider_evidence_refs") or []
                    )
                target_method = next(
                    (
                        item
                        for item in target_symbol.get("methods", [])
                        if item["name"] == call["target_method"]
                    ),
                    None,
                )
                rows.append(
                    {
                        "source_file": source_file,
                        "source_class": method["class_name"],
                        "source_method": method["name"],
                        "receiver_name": call["receiver"],
                        "declared_type": declared_type,
                        "imported_symbol": str(
                            (imported or {}).get("imported") or ""
                        ),
                        "resolved_file": str(
                            target_symbol.get("file") or ""
                        ),
                        "resolved_class": str(
                            target_symbol.get("name") or ""
                        ),
                        "resolved_method": (
                            call["target_method"] if target else ""
                        ),
                        "resolution_status": status,
                        "resolution_depth": int(
                            (target or {}).get("depth") or 0
                        ),
                        "confidence": (
                            0.92
                            if status.startswith("resolved_")
                            else 0.45
                        ),
                        "callsite_line": call["line"],
                        "db_operation_ids": [
                            item.get("operation_id")
                            for item in db_operations
                            if item.get("operation_id")
                        ],
                        "import_evidence_refs": import_refs,
                        "dependency_evidence_refs": dependency.get(
                            "evidence_refs", []
                        ),
                        "callsite_evidence_refs": [
                            source_ref(
                                source_file,
                                call["line"],
                                call["snippet"],
                                "transaction_callsite",
                            )
                        ],
                        "target_evidence_refs": (
                            target_method.get("evidence_refs", [])
                            if target_method
                            else target_symbol.get("evidence_refs", [])
                        ),
                        "limitations": sorted(set(limitations)),
                    }
                )
    rows = stable_sort_resolutions(rows)
    unique = {}
    for item in rows:
        key = (
            item["source_file"],
            item["source_class"],
            item["source_method"],
            item["receiver_name"],
            item["callsite_line"],
            item["resolved_file"],
            item["resolved_class"],
            item["resolved_method"],
            item["resolution_status"],
        )
        unique.setdefault(key, item)
    return stable_sort_resolutions(unique.values()), max(
        0, len(rows) - len(unique)
    )
