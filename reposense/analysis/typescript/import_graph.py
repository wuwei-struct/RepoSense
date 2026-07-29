from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from .import_graph_schema import normalize_relative_path, stable_id


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
MAX_RESOLUTION_DEPTH = 3


def source_ref(file_name, line, snippet, source_type):
    if not file_name or not isinstance(line, int) or line < 1:
        return None
    return {
        "source_type": source_type,
        "file": normalize_relative_path(file_name),
        "start_line": line,
        "end_line": line,
        "snippet": str(snippet or "").strip()[:500],
    }


def _iter_files(repo_root):
    for path in sorted(repo_root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file() or path.suffix.lower() not in {".ts", ".tsx"}:
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        yield path


def _line_at(text, offset):
    return text.count("\n", 0, offset) + 1


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


def _matching_paren(text, start):
    depth = 0
    quote = ""
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if quote:
            if char == quote and not escaped:
                quote = ""
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
            continue
        if char in {"'", '"', "`"}:
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
    return -1


def _split_top_level(value):
    rows = []
    start = 0
    depths = {"(": 0, "[": 0, "{": 0, "<": 0}
    pairs = {")": "(", "]": "[", "}": "{", ">": "<"}
    quote = ""
    for index, char in enumerate(value):
        if quote:
            if char == quote and (index == 0 or value[index - 1] != "\\"):
                quote = ""
            continue
        if char in {"'", '"', "`"}:
            quote = char
        elif char in depths:
            depths[char] += 1
        elif char in pairs and depths[pairs[char]] > 0:
            depths[pairs[char]] -= 1
        elif char == "," and not any(depths.values()):
            rows.append(value[start:index])
            start = index + 1
    rows.append(value[start:])
    return rows


def _module_file(repo_root, source_file, module):
    if not str(module).startswith("."):
        return ""
    source = repo_root / Path(source_file)
    base = source.parent / module
    candidates = []
    if base.suffix.lower() in {".ts", ".tsx"}:
        candidates.append(base)
    else:
        candidates.extend(
            [
                Path(str(base) + ".ts"),
                Path(str(base) + ".tsx"),
                base / "index.ts",
                base / "index.tsx",
            ]
        )
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
            relative = resolved.relative_to(repo_root.resolve())
        except (OSError, ValueError):
            continue
        if resolved.is_file():
            return relative.as_posix()
    return ""


def _parse_imports(file_name, text, lines, repo_root):
    rows = []
    import_re = re.compile(
        r"import\s+(?P<body>[\s\S]*?)\s+from\s*['\"](?P<module>[^'\"]+)['\"]\s*;?"
    )
    for match in import_re.finditer(text):
        body = match.group("body").strip()
        module = match.group("module")
        line = _line_at(text, match.start())
        module_file = _module_file(repo_root, file_name, module)
        evidence = source_ref(file_name, line, lines[line - 1], "typescript_import")
        if body.startswith("{"):
            named = body[1 : body.rfind("}")]
        elif ", {" in body:
            prefix, named = body.split(",", 1)
            named = named[named.find("{") + 1 : named.rfind("}")]
            rows.append(
                {
                    "kind": "default",
                    "local": prefix.strip(),
                    "imported": "default",
                    "module": module,
                    "module_file": module_file,
                    "line": line,
                    "evidence_refs": [evidence] if evidence else [],
                }
            )
        elif body.startswith("*"):
            namespace = re.search(r"\*\s+as\s+([A-Za-z_$][A-Za-z0-9_$]*)", body)
            if namespace:
                rows.append(
                    {
                        "kind": "namespace",
                        "local": namespace.group(1),
                        "imported": "*",
                        "module": module,
                        "module_file": module_file,
                        "line": line,
                        "evidence_refs": [evidence] if evidence else [],
                    }
                )
            continue
        else:
            rows.append(
                {
                    "kind": "default",
                    "local": body,
                    "imported": "default",
                    "module": module,
                    "module_file": module_file,
                    "line": line,
                    "evidence_refs": [evidence] if evidence else [],
                }
            )
            continue
        for raw in named.split(","):
            bits = re.split(r"\s+as\s+", raw.strip())
            original = bits[0].strip()
            local = bits[-1].strip()
            if original and local:
                rows.append(
                    {
                        "kind": "named",
                        "local": local,
                        "imported": original,
                        "module": module,
                        "module_file": module_file,
                        "line": line,
                        "evidence_refs": [evidence] if evidence else [],
                    }
                )
    return rows


def _parse_reexports(file_name, text, lines, repo_root):
    rows = []
    for match in re.finditer(
        r"export\s*\{(?P<body>[^}]+)\}\s*from\s*['\"](?P<module>[^'\"]+)['\"]",
        text,
        re.MULTILINE | re.DOTALL,
    ):
        line = _line_at(text, match.start())
        evidence = source_ref(file_name, line, lines[line - 1], "typescript_reexport")
        for raw in match.group("body").split(","):
            bits = re.split(r"\s+as\s+", raw.strip())
            imported = bits[0].strip()
            exported = bits[-1].strip()
            if imported and exported:
                rows.append(
                    {
                        "kind": "named",
                        "imported": imported,
                        "exported": exported,
                        "module": match.group("module"),
                        "module_file": _module_file(
                            repo_root, file_name, match.group("module")
                        ),
                        "line": line,
                        "evidence_refs": [evidence] if evidence else [],
                    }
                )
    for match in re.finditer(
        r"export\s+\*\s+from\s*['\"](?P<module>[^'\"]+)['\"]",
        text,
    ):
        line = _line_at(text, match.start())
        evidence = source_ref(file_name, line, lines[line - 1], "typescript_reexport")
        rows.append(
            {
                "kind": "star",
                "imported": "*",
                "exported": "*",
                "module": match.group("module"),
                "module_file": _module_file(
                    repo_root, file_name, match.group("module")
                ),
                "line": line,
                "evidence_refs": [evidence] if evidence else [],
            }
        )
    return rows


def _class_ranges(file_name, text, lines):
    rows = []
    pattern = re.compile(
        r"(?P<export>export\s+)?(?P<default>default\s+)?"
        r"(?P<abstract>abstract\s+)?(?P<kind>class|interface)\s+"
        r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)[^{]*\{"
    )
    for match in pattern.finditer(text):
        line = _line_at(text, match.start())
        ref = source_ref(file_name, line, lines[line - 1], "typescript_symbol")
        rows.append(
            {
                "name": match.group("name"),
                "kind": match.group("kind"),
                "abstract": bool(match.group("abstract")),
                "export_kind": (
                    "default"
                    if match.group("default")
                    else "named"
                    if match.group("export")
                    else "local"
                ),
                "start": line,
                "end": _brace_end(lines, line - 1),
                "evidence_refs": [ref] if ref else [],
            }
        )
    return rows


def _method_ranges(file_name, lines, classes):
    rows = []
    method_re = re.compile(
        r"^\s*(?:(?:public|private|protected|static|async|readonly|override|abstract)\s+)*"
        r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*(?:<[^>{}]+>)?\s*\("
        r"[\s\S]*?\)\s*(?::[^={]+)?\s*\{"
    )
    for index, line in enumerate(lines):
        if not line.strip() or line.lstrip().startswith("@"):
            continue
        statement = "\n".join(lines[index : min(len(lines), index + 18)])
        match = method_re.search(statement)
        if not match or match.group("name") in {
            "if",
            "for",
            "while",
            "switch",
            "catch",
            "constructor",
        }:
            continue
        line_no = index + 1
        owner = next(
            (
                item
                for item in classes
                if item["kind"] == "class"
                and item["start"] <= line_no <= item["end"]
            ),
            None,
        )
        if owner is None:
            continue
        ref = source_ref(file_name, line_no, lines[line_no - 1], "typescript_method")
        rows.append(
            {
                "name": match.group("name"),
                "class_name": owner["name"],
                "start": line_no,
                "end": _brace_end(lines, index),
                "evidence_refs": [ref] if ref else [],
            }
        )
    return rows


def _constructor_dependencies(file_name, text, lines, classes):
    rows = defaultdict(list)
    for match in re.finditer(r"\bconstructor\s*\(", text):
        open_at = match.end() - 1
        close_at = _matching_paren(text, open_at)
        if close_at < 0:
            continue
        constructor_line = _line_at(text, match.start())
        owner = next(
            (
                item
                for item in classes
                if item["kind"] == "class"
                and item["start"] <= constructor_line <= item["end"]
            ),
            None,
        )
        if owner is None:
            continue
        params = text[open_at + 1 : close_at]
        search_at = 0
        for raw in _split_top_level(params):
            raw_at = params.find(raw, search_at)
            search_at = max(search_at, raw_at + len(raw))
            value = raw.strip()
            if not value:
                continue
            inject = re.search(r"@Inject\s*\(\s*([^)]+)\)", value, re.DOTALL)
            value = re.sub(r"@[A-Za-z_$][A-Za-z0-9_$.]*\s*\([^)]*\)", "", value)
            value = re.sub(
                r"\b(?:private|public|protected|readonly|override)\b", "", value
            )
            dep = re.search(
                r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*[!?]?\s*:\s*"
                r"(?P<type>[A-Za-z_$][A-Za-z0-9_$.]*(?:\s*<[^>]+>)?)",
                value,
            )
            if not dep:
                continue
            name_at = raw.find(dep.group("name"))
            line = _line_at(
                text,
                open_at + 1 + max(0, raw_at) + max(0, name_at),
            )
            declared = re.sub(r"\s*<.*>$", "", dep.group("type")).strip()
            ref = source_ref(
                file_name,
                line,
                lines[line - 1],
                "constructor_dependency",
            )
            rows[owner["name"]].append(
                {
                    "name": dep.group("name"),
                    "declared_type": declared,
                    "line": line,
                    "dynamic_inject_token": inject.group(1).strip() if inject else "",
                    "evidence_refs": [ref] if ref else [],
                }
            )
    return rows


def _properties(file_name, lines, classes):
    rows = defaultdict(list)
    pattern = re.compile(
        r"(?:private|protected|public)?\s*(?:readonly\s+)?"
        r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*[!?]?\s*:\s*"
        r"(?P<type>[A-Za-z_$][A-Za-z0-9_$.]*(?:\s*<[^>]+>)?)"
    )
    for owner in classes:
        if owner["kind"] != "class":
            continue
        for line_no in range(owner["start"], owner["end"] + 1):
            line = lines[line_no - 1]
            match = pattern.search(line)
            if not match:
                continue
            ref = source_ref(file_name, line_no, line, "typescript_property")
            rows[owner["name"]].append(
                {
                    "name": match.group("name"),
                    "declared_type": re.sub(
                        r"\s*<.*>$", "", match.group("type")
                    ).strip(),
                    "line": line_no,
                    "evidence_refs": [ref] if ref else [],
                }
            )
    return rows


def _parse_providers(file_name, text, lines):
    rows = []
    for match in re.finditer(
        r"\{[\s\S]{0,240}?\bprovide\s*:\s*"
        r"(?P<provide>[A-Za-z_$][A-Za-z0-9_$.]*)\s*,"
        r"[\s\S]{0,160}?\buseClass\s*:\s*"
        r"(?P<use_class>[A-Za-z_$][A-Za-z0-9_$.]*)[\s\S]{0,80}?\}",
        text,
    ):
        line = _line_at(text, match.start())
        ref = source_ref(file_name, line, lines[line - 1], "nestjs_provider")
        rows.append(
            {
                "provide": match.group("provide").split(".")[-1],
                "use_class": match.group("use_class").split(".")[-1],
                "line": line,
                "evidence_refs": [ref] if ref else [],
            }
        )
    return rows


def build_typescript_index(repo_path):
    repo_root = Path(repo_path).expanduser().resolve()
    files = {}
    symbols = []
    providers = []
    for path in _iter_files(repo_root):
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError):
            continue
        relative = path.resolve().relative_to(repo_root).as_posix()
        lines = text.splitlines()
        classes = _class_ranges(relative, text, lines)
        methods = _method_ranges(relative, lines, classes)
        dependencies = _constructor_dependencies(relative, text, lines, classes)
        properties = _properties(relative, lines, classes)
        imports = _parse_imports(relative, text, lines, repo_root)
        reexports = _parse_reexports(relative, text, lines, repo_root)
        providers.extend(
            {"file": relative, **row}
            for row in _parse_providers(relative, text, lines)
        )
        files[relative] = {
            "file": relative,
            "text": text,
            "lines": lines,
            "imports": imports,
            "reexports": reexports,
            "classes": classes,
            "methods": methods,
            "constructor_dependencies": dependencies,
            "properties": properties,
        }
        for item in classes:
            class_methods = [
                method
                for method in methods
                if method["class_name"] == item["name"]
            ]
            symbols.append(
                {
                    "symbol_id": stable_id(
                        "ts-symbol", relative, item["kind"], item["name"]
                    ),
                    "name": item["name"],
                    "kind": item["kind"],
                    "file": relative,
                    "export_kind": item["export_kind"],
                    "abstract": item["abstract"],
                    "constructor_dependencies": dependencies.get(item["name"], []),
                    "properties": properties.get(item["name"], []),
                    "methods": class_methods,
                    "evidence_refs": item["evidence_refs"],
                    "limitations": [],
                }
            )
    symbols.sort(key=lambda item: (item["file"], item["name"], item["kind"]))
    providers.sort(
        key=lambda item: (
            item["file"],
            item["line"],
            item["provide"],
            item["use_class"],
        )
    )
    graph_files = [
        {
            "file": file_name,
            "imports": files[file_name]["imports"],
            "reexports": files[file_name]["reexports"],
        }
        for file_name in sorted(files)
    ]
    return {
        "repo_root": repo_root,
        "files": files,
        "symbols": symbols,
        "providers": providers,
        "import_graph": {
            "version": "typescript_import_graph_v1",
            "max_resolution_depth": MAX_RESOLUTION_DEPTH,
            "files": graph_files,
            "limitations": [
                "Only repository-relative TypeScript imports are resolved.",
                "tsconfig, bundler, package, and runtime dependency aliases remain unresolved.",
                "Re-export traversal is cycle-safe and limited to three edges.",
            ],
        },
        "symbol_index": {
            "version": "typescript_symbol_index_v1",
            "symbols": symbols,
            "limitations": [
                "The symbol index is a conservative static subset, not a complete TypeScript grammar.",
                "Dynamic dependency injection and runtime provider selection are not modeled.",
            ],
        },
    }


def _declared_symbols(index, file_name, symbol_name):
    return [
        item
        for item in index["symbols"]
        if item["file"] == file_name
        and (
            item["name"] == symbol_name
            or (symbol_name == "default" and item["export_kind"] == "default")
        )
        and item["export_kind"] in {"named", "default"}
    ]


def resolve_export(index, file_name, symbol_name, depth=0, visited=None):
    visited = set(visited or set())
    key = (file_name, symbol_name)
    if key in visited:
        return [], ["reexport_cycle_detected"]
    if depth > MAX_RESOLUTION_DEPTH:
        return [], ["cross_file_resolution_depth_exceeded"]
    visited.add(key)
    direct = _declared_symbols(index, file_name, symbol_name)
    if direct:
        return [
            {
                "symbol": item,
                "depth": depth,
                "path": [file_name],
                "reexport_evidence_refs": [],
            }
            for item in direct
        ], []
    parsed = index["files"].get(file_name)
    if not parsed:
        return [], ["receiver_type_unresolved"]
    results = []
    limitations = []
    for edge in parsed["reexports"]:
        if not edge.get("module_file"):
            continue
        next_symbol = ""
        if edge["kind"] == "named" and edge["exported"] == symbol_name:
            next_symbol = edge["imported"]
        elif edge["kind"] == "star":
            next_symbol = symbol_name
        if not next_symbol:
            continue
        nested, nested_limits = resolve_export(
            index,
            edge["module_file"],
            next_symbol,
            depth + 1,
            set(visited),
        )
        for item in nested:
            item = dict(item)
            item["path"] = [file_name] + list(item["path"])
            item["reexport_evidence_refs"] = list(
                edge.get("evidence_refs") or []
            ) + list(item.get("reexport_evidence_refs") or [])
            results.append(item)
        limitations.extend(nested_limits)
    unique = {}
    for item in results:
        symbol = item["symbol"]
        unique[(symbol["file"], symbol["name"])] = item
    return list(unique.values()), sorted(set(limitations))


def resolve_type(index, source_file, declared_type):
    parsed = index["files"].get(source_file)
    if not parsed:
        return [], None, ["receiver_type_unresolved"]
    namespace, _, member = declared_type.partition(".")
    for item in parsed["imports"]:
        imported_symbol = ""
        if item["kind"] == "namespace" and member and item["local"] == namespace:
            imported_symbol = member
        elif not member and item["local"] == declared_type:
            imported_symbol = item["imported"]
        if not imported_symbol:
            continue
        if not item.get("module_file"):
            limitation = (
                "typescript_path_alias_unresolved"
                if not str(item.get("module") or "").startswith(".")
                else "receiver_type_unresolved"
            )
            return [], item, [limitation]
        results, limitations = resolve_export(
            index, item["module_file"], imported_symbol
        )
        return results, item, limitations
    local = [
        item
        for item in index["symbols"]
        if item["file"] == source_file and item["name"] == declared_type
    ]
    if local:
        return [
            {
                "symbol": item,
                "depth": 0,
                "path": [source_file],
                "reexport_evidence_refs": [],
            }
            for item in local
        ], None, []
    return [], None, ["receiver_type_unresolved"]
