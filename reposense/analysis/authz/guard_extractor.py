import json
import os
import re

import yaml

from ...linking.path_normalize import normalize_path
from ..routes.typescript_decorator_classifier import (
    classify_typescript_decorators,
)
from .authz_rules import SKIP_DIRS
from .guard_correlation_schema import stable_id


NEST_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx"}
USE_GUARDS_RE = re.compile(r"@UseGuards\s*\(", re.I)
PUBLIC_DECORATOR_RE = re.compile(r"@(Public|AllowAnonymous|SkipAuth)\s*\(", re.I)
OPENAPI_NAMES = ("openapi", "swagger")
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _rel(root, path):
    return os.path.relpath(path, root).replace("\\", "/")


def _iter_files(repo_path, extensions=None):
    root = os.path.abspath(repo_path)
    for current, dirs, files in os.walk(root):
        dirs[:] = [
            name
            for name in dirs
            if name not in SKIP_DIRS
            and not name.startswith(".reposense_")
            and name not in {"analysis_runs", ".mypy_cache"}
        ]
        for name in sorted(files):
            if extensions and os.path.splitext(name)[1].lower() not in extensions:
                continue
            yield _rel(root, os.path.join(current, name)), os.path.join(current, name)


def _read_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read().splitlines()
    except OSError:
        return []


def _evidence(source_type, file_path, line, snippet):
    if not file_path or int(line or 0) < 1:
        return []
    return [
        {
            "source_type": source_type,
            "file": str(file_path).replace("\\", "/"),
            "start_line": int(line),
            "end_line": int(line),
            "snippet": str(snippet or "")[:500],
        }
    ]


def _join_path(prefix, method_path):
    prefix = normalize_path(prefix)
    method_path = normalize_path(method_path)
    if prefix == "/":
        return method_path
    if method_path == "/":
        return prefix
    return normalize_path(prefix.rstrip("/") + "/" + method_path.lstrip("/"))


def _join_raw_path(prefix, method_path):
    prefix = "/" + str(prefix or "").strip("/")
    method_path = str(method_path or "").strip("/")
    if not method_path:
        return prefix or "/"
    if prefix == "/":
        return "/" + method_path
    return prefix.rstrip("/") + "/" + method_path


def _guard_type(name):
    low = str(name or "").lower()
    if "permission" in low or "policy" in low or "ability" in low:
        return "permission"
    if "role" in low:
        return "role"
    if "auth" in low or "jwt" in low or "passport" in low or "session" in low:
        return "auth"
    return "unknown"


def _split_arguments(raw):
    parts = []
    current = []
    depth = 0
    quote = ""
    for char in str(raw or ""):
        if quote:
            current.append(char)
            if char == quote:
                quote = ""
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
        elif char in "([{":
            depth += 1
            current.append(char)
        elif char in ")]}":
            depth = max(0, depth - 1)
            current.append(char)
        elif char == "," and depth == 0:
            if "".join(current).strip():
                parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if "".join(current).strip():
        parts.append("".join(current).strip())
    return parts


def _guard_entries(raw, scope, file_path, line, snippet):
    entries = []
    for token in _split_arguments(raw):
        name = re.sub(r"^\s*new\s+", "", token.strip())
        if not re.match(r"^[A-Za-z_$][A-Za-z0-9_$]*(?:\s*\(|$)", name):
            continue
        gtype = _guard_type(name)
        entries.append(
            {
                "guard_id": stable_id("guard-source", scope, file_path, line, name),
                "guard_name": name,
                "guard_type": gtype,
                "scope": scope,
                "file": file_path,
                "line_start": int(line),
                "confidence": 0.94 if gtype != "unknown" else 0.65,
                "evidence_refs": _evidence("route_guard", file_path, line, snippet),
                "limitations": [] if gtype != "unknown" else ["guard_type_unresolved"],
            }
        )
    return entries


def _public_entries(decorators, scope, file_path, definitions):
    rows = []
    for item in decorators:
        match = PUBLIC_DECORATOR_RE.search(item["text"])
        if not match:
            continue
        name = match.group(1)
        definition = definitions.get(name.lower())
        limitations = []
        confidence = 0.93
        refs = _evidence("public_bypass", file_path, item["line"], item["text"])
        metadata_key = ""
        if definition:
            refs += definition.get("evidence_refs") or []
            metadata_key = str(definition.get("metadata_key") or "")
            if not definition.get("guard_reads_key"):
                confidence = 0.82
                limitations.append("public_metadata_guard_reader_unresolved")
        else:
            confidence = 0.65
            limitations.append("public_decorator_definition_unresolved")
        rows.append(
            {
                "bypass_id": stable_id("public-bypass", scope, file_path, item["line"], name),
                "decorator": name,
                "scope": scope,
                "file": file_path,
                "line_start": item["line"],
                "metadata_key": metadata_key,
                "confidence": confidence,
                "evidence_refs": refs,
                "limitations": limitations,
            }
        )
    return rows


def _decorator_definitions(repo_path):
    raw_defs = {}
    guard_text = []
    key_values = {}
    for rel, path in _iter_files(repo_path, NEST_EXTENSIONS):
        lines = _read_lines(path)
        text = "\n".join(lines)
        guard_text.append(text)
        for index, line in enumerate(lines, 1):
            key_match = re.search(
                r"(?:export\s+)?const\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*['\"]([^'\"]+)['\"]",
                line,
            )
            if key_match:
                key_values[key_match.group(1)] = key_match.group(2)
            definition = re.search(
                r"(?:export\s+)?const\s+(Public|AllowAnonymous|SkipAuth)\b.*SetMetadata\s*\(\s*([^,\)]+)",
                line,
                re.I,
            )
            if definition:
                token = definition.group(2).strip().strip("'\"")
                raw_defs[definition.group(1).lower()] = {
                    "name": definition.group(1),
                    "metadata_token": token,
                    "file": rel,
                    "line_start": index,
                    "evidence_refs": _evidence("public_decorator_definition", rel, index, line.strip()),
                }
    combined = "\n".join(guard_text)
    for row in raw_defs.values():
        token = row.pop("metadata_token")
        key = key_values.get(token, token)
        row["metadata_key"] = key
        row["guard_reads_key"] = bool(
            re.search(
                rf"(getAllAndOverride|getAllAndMerge|get)\s*<[^>]*>\s*\(\s*{re.escape(token)}\b"
                rf"|(getAllAndOverride|getAllAndMerge|get)\s*\(\s*['\"]{re.escape(key)}['\"]",
                combined,
                re.I,
            )
        )
    return raw_defs


def _pending_guards(decorators, scope, file_path):
    rows = []
    for item in decorators:
        text = item["text"]
        match = USE_GUARDS_RE.search(text)
        if match:
            start = text.find("(", match.start())
            end = text.rfind(")")
            raw = text[start + 1 : end] if start >= 0 and end > start else ""
            rows.extend(
                _guard_entries(
                    raw,
                    scope,
                    file_path,
                    item["line"],
                    item["text"],
                )
            )
    return rows


def _call_arguments(text, marker_start):
    start = text.find("(", marker_start)
    if start < 0:
        return "", start
    depth = 0
    quote = ""
    for index in range(start, len(text)):
        char = text[index]
        if quote:
            if char == quote and text[index - 1 : index] != "\\":
                quote = ""
            continue
        if char in {"'", '"'}:
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[start + 1 : index], index
    return "", start


def _extract_file_routes(rel, lines, definitions):
    routes = []
    guards = []
    bypasses = []
    classified = classify_typescript_decorators(lines, rel)
    for canonical in classified["routes"]:
        method_decorators = canonical.get("method_decorators") or []
        controller_decorators = canonical.get("controller_decorators") or []
        method_guards = _pending_guards(method_decorators, "method", rel)
        controller_guards = _pending_guards(
            controller_decorators,
            "controller",
            rel,
        )
        method_bypasses = _public_entries(
            method_decorators,
            "method",
            rel,
            definitions,
        )
        controller_bypasses = _public_entries(
            controller_decorators,
            "controller",
            rel,
            definitions,
        )
        guards.extend(method_guards)
        guards.extend(controller_guards)
        bypasses.extend(method_bypasses)
        bypasses.extend(controller_bypasses)
        route = dict(canonical)
        route["method_guards"] = method_guards
        route["controller_guards"] = controller_guards
        route["method_bypasses"] = method_bypasses
        route["controller_bypasses"] = controller_bypasses
        routes.append(route)
    return routes, guards, bypasses


def _extract_global_guards(repo_path):
    guards = []
    for rel, path in _iter_files(repo_path, NEST_EXTENSIONS):
        lines = _read_lines(path)
        text = "\n".join(lines)
        for direct in re.finditer(r"\bapp\.useGlobalGuards\s*\(", text, re.I):
            raw, end = _call_arguments(text, direct.start())
            if end <= direct.start():
                continue
            line = text.count("\n", 0, direct.start()) + 1
            snippet = " ".join(text[direct.start() : end + 1].split())
            guards.extend(
                _guard_entries(raw, "global", rel, line, snippet)
            )
        for index, line in enumerate(lines, 1):
            if re.search(r"\bprovide\s*:\s*APP_GUARD\b", line):
                window = lines[max(0, index - 4) : min(len(lines), index + 8)]
                window_text = "\n".join(window)
                provider = re.search(
                    r"\b(?:useClass|useExisting)\s*:\s*([A-Za-z_$][A-Za-z0-9_$]*)",
                    window_text,
                )
                factory = re.search(r"\buseFactory\s*:", window_text)
                name = provider.group(1) if provider else ("useFactory" if factory else "APP_GUARD")
                entries = _guard_entries(name, "global", rel, index, line.strip())
                for entry in entries:
                    entry["evidence_refs"] = _evidence("global_guard", rel, index, line.strip())
                    if not provider:
                        entry["confidence"] = min(float(entry["confidence"]), 0.7)
                        entry["limitations"] = sorted(
                            set((entry.get("limitations") or []) + ["global_guard_provider_unresolved"])
                        )
                guards.extend(entries)
    unique = {}
    for row in guards:
        unique[row["guard_id"]] = row
    return sorted(unique.values(), key=lambda row: (row["file"], row["line_start"], row["guard_id"]))


def extract_nestjs_guards(repo_path):
    definitions = _decorator_definitions(repo_path)
    routes = []
    guards = []
    bypasses = []
    for rel, path in _iter_files(repo_path, NEST_EXTENSIONS):
        file_routes, file_guards, file_bypasses = _extract_file_routes(
            rel,
            _read_lines(path),
            definitions,
        )
        routes.extend(file_routes)
        guards.extend(file_guards)
        bypasses.extend(file_bypasses)
    global_guards = _extract_global_guards(repo_path)
    routes.sort(key=lambda row: (row["method"], row["path"], row["file"], row["line_start"]))
    guards = sorted(
        {row["guard_id"]: row for row in guards}.values(),
        key=lambda row: (row["scope"], row["file"], row["line_start"], row["guard_id"]),
    )
    bypasses = sorted(
        {row["bypass_id"]: row for row in bypasses}.values(),
        key=lambda row: (row["scope"], row["file"], row["line_start"], row["bypass_id"]),
    )
    return {
        "version": "nestjs_guard_surface_v1",
        "routes": routes,
        "guards": guards,
        "global_guards": global_guards,
        "public_bypasses": bypasses,
        "public_decorator_definitions": sorted(
            definitions.values(),
            key=lambda row: (row["file"], row["line_start"], row["name"]),
        ),
        "limitations": [
            "NestJS module boundaries are inferred conservatively; a complete module dependency graph is not built.",
            "Custom runtime Guard behavior is not executed or proven.",
        ],
    }


def _openapi_line_map(lines):
    path_lines = {}
    operation_lines = {}
    in_paths = False
    current_path = ""
    for index, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped == "paths:":
            in_paths = True
            continue
        if not in_paths:
            continue
        path_match = re.match(r"^\s{0,8}(/[^:\s]+)\s*:\s*$", line)
        if path_match:
            current_path = path_match.group(1)
            path_lines[current_path] = index
            continue
        method_match = re.match(r"^\s{2,16}(get|post|put|patch|delete)\s*:\s*$", line, re.I)
        if method_match and current_path:
            operation_lines[(method_match.group(1).upper(), current_path)] = index
    return path_lines, operation_lines


def _security_names(value):
    if not isinstance(value, list):
        return []
    names = []
    for item in value:
        if isinstance(item, dict):
            names.extend(str(name) for name in item.keys())
    return sorted(set(names))


def extract_openapi_security(repo_path):
    specs = []
    routes = []
    scheme_names = set()
    for rel, path in _iter_files(repo_path, {".yaml", ".yml", ".json"}):
        if not any(name in os.path.basename(rel).lower() for name in OPENAPI_NAMES):
            continue
        lines = _read_lines(path)
        try:
            if rel.lower().endswith(".json"):
                with open(path, "r", encoding="utf-8") as handle:
                    obj = json.load(handle)
            else:
                with open(path, "r", encoding="utf-8") as handle:
                    obj = yaml.safe_load(handle)
        except (OSError, ValueError, yaml.YAMLError):
            continue
        if not isinstance(obj, dict) or not obj.get("openapi"):
            continue
        path_lines, operation_lines = _openapi_line_map(lines)
        components = obj.get("components") if isinstance(obj.get("components"), dict) else {}
        schemes = components.get("securitySchemes") if isinstance(components.get("securitySchemes"), dict) else {}
        scheme_names.update(str(name) for name in schemes.keys())
        global_security_present = "security" in obj
        global_security = obj.get("security") if global_security_present else None
        global_names = _security_names(global_security)
        specs.append(
            {
                "file": rel,
                "global_security_declared": global_security_present,
                "global_security": global_security if isinstance(global_security, list) else [],
                "security_scheme_names": sorted(str(name) for name in schemes.keys()),
                "evidence_refs": _evidence(
                    "openapi_security",
                    rel,
                    next((index for index, line in enumerate(lines, 1) if line.strip().startswith("security:")), 1),
                    "OpenAPI security declaration",
                ),
            }
        )
        paths = obj.get("paths") if isinstance(obj.get("paths"), dict) else {}
        for raw_path in sorted(paths.keys()):
            path_item = paths.get(raw_path)
            if not isinstance(path_item, dict):
                continue
            for method in sorted(path_item.keys()):
                if str(method).lower() not in HTTP_METHODS:
                    continue
                operation = path_item.get(method)
                if not isinstance(operation, dict):
                    operation = {}
                operation_declared = "security" in operation
                operation_security = operation.get("security") if operation_declared else None
                if operation_declared and operation_security == []:
                    status = "public"
                    names = []
                elif operation_declared:
                    status = "protected"
                    names = _security_names(operation_security)
                elif global_security_present and global_security == []:
                    status = "public"
                    names = []
                elif global_security_present:
                    status = "protected"
                    names = global_names
                else:
                    status = "unspecified"
                    names = []
                method_upper = str(method).upper()
                line = operation_lines.get((method_upper, raw_path)) or path_lines.get(raw_path) or 1
                routes.append(
                    {
                        "route_id": stable_id("openapi-route", method_upper, normalize_path(raw_path), rel, line),
                        "method": method_upper,
                        "path": normalize_path(raw_path),
                        "raw_path": str(raw_path),
                        "file": rel,
                        "line_start": int(line),
                        "security_status": status,
                        "security_scheme_names": names,
                        "operation_security_declared": operation_declared,
                        "explicit_public": operation_declared and operation_security == [],
                        "source_refs": _evidence(
                            "openapi_security",
                            rel,
                            line,
                            f"{method_upper} {normalize_path(raw_path)} security={status}",
                        ),
                    }
                )
    routes.sort(key=lambda row: (row["method"], row["path"], row["file"], row["line_start"]))
    specs.sort(key=lambda row: row["file"])
    return {
        "version": "openapi_security_surface_v1",
        "specs": specs,
        "routes": routes,
        "security_scheme_names": sorted(scheme_names),
        "limitations": [
            "OpenAPI security is contract/documentation evidence, not implementation guard proof.",
            "OpenAPI files are identified conservatively by openapi/swagger file names.",
        ],
    }
