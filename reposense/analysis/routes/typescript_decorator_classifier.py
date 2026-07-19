import os
import re

from ...linking.path_normalize import normalize_path
from .decorator_schema import (
    ROUTE_DECORATORS,
    evidence_ref,
    normalize_classification,
    stable_id,
    summarize_classifications,
)


TYPESCRIPT_EXTENSIONS = {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx"}
SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".tmp_test_runs",
    ".reposense_ci",
    ".reposense_demo",
    ".reposense_release_demo",
}
KNOWN_NON_ROUTE_DECORATORS = {
    "DeleteDateColumn",
    "CreateDateColumn",
    "UpdateDateColumn",
    "Column",
    "PrimaryColumn",
    "PrimaryGeneratedColumn",
    "Entity",
    "Index",
    "ManyToOne",
    "OneToMany",
    "OneToOne",
    "ManyToMany",
    "JoinColumn",
    "JoinTable",
    "BeforeInsert",
    "BeforeUpdate",
    "AfterLoad",
    "ApiProperty",
    "ApiOperation",
    "ApiResponse",
    "ApiTags",
    "ApiBearerAuth",
    "ApiParam",
    "ApiQuery",
    "IsString",
    "IsOptional",
    "ValidateNested",
    "Type",
    "Transform",
    "Expose",
    "Exclude",
    "Body",
    "Param",
    "Query",
    "Headers",
    "Req",
    "Res",
    "Inject",
    "Injectable",
    "Module",
    "UseGuards",
    "UseInterceptors",
    "SetMetadata",
}
LIMITATIONS = [
    "Decorator targets are classified with a conservative lexical parser, not a complete TypeScript AST.",
    "Computed decorator aliases and dynamically constructed decorators are not resolved.",
    "Unknown decorator contexts do not produce canonical route facts.",
]

DECORATOR_NAME_RE = re.compile(r"@([A-Za-z_$][A-Za-z0-9_$]*)\b")
CLASS_RE = re.compile(
    r"^(?:(?:export|default|abstract|declare)\s+)*class\s+"
    r"([A-Za-z_$][A-Za-z0-9_$]*)\b"
)
METHOD_RE = re.compile(
    r"^(?:(?:public|private|protected|static|async|abstract|override)\s+)*"
    r"(?:get\s+|set\s+)?([A-Za-z_$][A-Za-z0-9_$]*)"
    r"\s*(?:<[^>{};]*>)?\s*\("
)
PROPERTY_RE = re.compile(
    r"^(?:(?:public|private|protected|static|readonly|declare|abstract)\s+)*"
    r"[A-Za-z_$][A-Za-z0-9_$]*\s*(?:[!?]\s*)?(?::|=|;)"
)


def _rel(root, path):
    return os.path.relpath(path, root).replace("\\", "/")


def _iter_files(repo_path):
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
            if os.path.splitext(name)[1].lower() not in TYPESCRIPT_EXTENSIONS:
                continue
            path = os.path.join(current, name)
            yield _rel(root, path), path


def _read_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read().splitlines()
    except OSError:
        return []


def _paren_delta(text):
    delta = 0
    quote = ""
    escaped = False
    for char in str(text or ""):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            continue
        if char in {"'", '"', "`"}:
            quote = char
        elif char == "(":
            delta += 1
        elif char == ")":
            delta -= 1
    return delta


def _brace_stats(text):
    delta = 0
    openings = 0
    quote = ""
    escaped = False
    index = 0
    value = str(text or "")
    while index < len(value):
        char = value[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            index += 1
            continue
        if char in {"'", '"', "`"}:
            quote = char
        elif char == "/" and index + 1 < len(value) and value[index + 1] == "/":
            break
        elif char == "{":
            delta += 1
            openings += 1
        elif char == "}":
            delta -= 1
        index += 1
    return delta, openings


def _class_scope_by_line(lines):
    scopes = {}
    active_class = ""
    depth = 0
    body_started = False
    for index, line in enumerate(lines, 1):
        stripped = line.strip()
        class_match = CLASS_RE.search(stripped)
        if class_match and not active_class:
            active_class = class_match.group(1)
            depth = 0
            body_started = False
        if not active_class:
            continue
        scopes[index] = active_class
        delta, openings = _brace_stats(line)
        if openings:
            body_started = True
        if body_started:
            depth += delta
            if depth <= 0:
                active_class = ""
                depth = 0
                body_started = False
    return scopes


def _parse_decorator(text, line_start, line_end=None):
    match = DECORATOR_NAME_RE.search(str(text or ""))
    if not match:
        return None
    return {
        "name": match.group(1),
        "text": " ".join(str(text or "").split()),
        "line": int(line_start),
        "line_end": int(line_end or line_start),
    }


def _decorators_in_text(text, line_start):
    items = []
    for match in DECORATOR_NAME_RE.finditer(str(text or "")):
        tail = str(text or "")[match.start() :]
        items.append(
            {
                "name": match.group(1),
                "text": " ".join(tail.split())[:500],
                "line": int(line_start),
                "line_end": int(line_start),
            }
        )
    return items


def _is_candidate(name):
    if name == "Controller" or name in ROUTE_DECORATORS:
        return True
    if name in KNOWN_NON_ROUTE_DECORATORS:
        return True
    return any(name.startswith(route_name) for route_name in ROUTE_DECORATORS)


def _literal_argument(text):
    match = re.search(r"\(\s*(['\"])(.*?)\1", str(text or ""), re.S)
    return match.group(2) if match else ""


def _controller_prefix(text):
    direct = _literal_argument(text)
    if direct:
        return direct
    object_path = re.search(
        r"\bpath\s*:\s*(['\"])(.*?)\1",
        str(text or ""),
        re.S,
    )
    return object_path.group(2) if object_path else ""


def _join_path(prefix, method_path):
    prefix_norm = normalize_path(prefix)
    method_norm = normalize_path(method_path)
    if prefix_norm == "/":
        return method_norm
    if method_norm == "/":
        return prefix_norm
    return normalize_path(
        prefix_norm.rstrip("/") + "/" + method_norm.lstrip("/")
    )


def _join_raw_path(prefix, method_path):
    prefix = "/" + str(prefix or "").strip("/")
    method_path = str(method_path or "").strip("/")
    if not method_path:
        return prefix or "/"
    if prefix == "/":
        return "/" + method_path
    return prefix.rstrip("/") + "/" + method_path


def _target_context(stripped):
    class_match = CLASS_RE.search(stripped)
    if class_match:
        return "class", class_match.group(1)
    method_match = METHOD_RE.search(stripped)
    if method_match:
        return "method", method_match.group(1)
    if PROPERTY_RE.search(stripped):
        return "property", ""
    return "unknown", ""


def _classification_row(item, file_path, context, classification, reason, method=""):
    return normalize_classification(
        {
            "file": file_path,
            "line_start": item["line"],
            "decorator_name": item["name"],
            "context": context,
            "classification": classification,
            "reason": reason,
            "route_method": method,
            "evidence_refs": evidence_ref(file_path, item["line"], item["text"]),
            "limitations": (
                ["decorator_context_unresolved"] if classification == "unknown" else []
            ),
        }
    )


def _classify_pending(
    pending,
    context,
    symbol,
    file_path,
    current_controller,
):
    rows = []
    controller = current_controller
    controller_item = next(
        (item for item in pending if item["name"] == "Controller"),
        None,
    )
    if context == "class":
        controller = {
            "class_name": symbol,
            "prefix": (
                _controller_prefix(controller_item["text"])
                if controller_item
                else ""
            ),
            "decorators": list(pending) if controller_item else [],
            "line": controller_item["line"] if controller_item else 0,
            "controller_observed": bool(controller_item),
        }

    for item in pending:
        name = item["name"]
        if not _is_candidate(name):
            continue
        if name == "Controller":
            accepted = context == "class"
            rows.append(
                _classification_row(
                    item,
                    file_path,
                    context,
                    "controller" if accepted else "non_route",
                    (
                        "Exact Controller decorator applied to a class."
                        if accepted
                        else "Controller decorator is not applied to a class."
                    ),
                )
            )
            continue
        if name in ROUTE_DECORATORS:
            method = ROUTE_DECORATORS[name]
            if context == "method" and controller:
                rows.append(
                    _classification_row(
                        item,
                        file_path,
                        context,
                        "route",
                        "Exact NestJS route decorator applied to a class method.",
                        method,
                    )
                )
            elif context == "unknown":
                rows.append(
                    _classification_row(
                        item,
                        file_path,
                        context,
                        "unknown",
                        "Exact route decorator target could not be resolved.",
                        method,
                    )
                )
            else:
                rows.append(
                    _classification_row(
                        item,
                        file_path,
                        context,
                        "non_route",
                        "Route decorator is not applied to a Controller method.",
                        method,
                    )
                )
            continue
        rows.append(
            _classification_row(
                item,
                file_path,
                context,
                "non_route",
                "Decorator symbol is not an exact NestJS route decorator.",
            )
        )
    return rows, controller


def classify_typescript_decorators(lines, file_path=""):
    rows = []
    routes = []
    pending = []
    collecting = None
    current_controller = None
    parameter_depth = 0
    class_scopes = _class_scope_by_line(lines)

    def finish_pending(context, symbol=""):
        nonlocal pending, current_controller
        classified, current_controller = _classify_pending(
            pending,
            context,
            symbol,
            file_path,
            current_controller,
        )
        rows.extend(classified)
        if context == "method" and current_controller:
            for item in pending:
                if item["name"] not in ROUTE_DECORATORS:
                    continue
                classification = next(
                    (
                        row
                        for row in classified
                        if row["line_start"] == item["line"]
                        and row["decorator_name"] == item["name"]
                    ),
                    {},
                )
                if classification.get("classification") != "route":
                    continue
                method_path = _literal_argument(item["text"])
                path = _join_path(current_controller["prefix"], method_path)
                routes.append(
                    {
                        "route_id": stable_id(
                            "canonical-nestjs-route",
                            ROUTE_DECORATORS[item["name"]],
                            path,
                            file_path,
                            item["line"],
                        ),
                        "framework": "nestjs",
                        "method": ROUTE_DECORATORS[item["name"]],
                        "path": path,
                        "raw_path": _join_raw_path(
                            current_controller["prefix"],
                            method_path,
                        ),
                        "file": str(file_path or "").replace("\\", "/"),
                        "line_start": item["line"],
                        "line_end": item["line_end"],
                        "handler_name": symbol,
                        "controller_class": current_controller["class_name"],
                        "controller_prefix": normalize_path(
                            current_controller["prefix"]
                        ),
                        "method_decorators": list(pending),
                        "controller_decorators": list(
                            current_controller["decorators"]
                        ),
                        "source_refs": evidence_ref(
                            file_path,
                            item["line"],
                            item["text"],
                        ),
                    }
                )
        pending = []

    for index, line in enumerate(lines, 1):
        stripped = line.strip()
        if collecting is not None:
            collecting["parts"].append(stripped)
            collecting["balance"] += _paren_delta(line)
            collecting["line_end"] = index
            if collecting["balance"] <= 0:
                parsed = _parse_decorator(
                    " ".join(collecting["parts"]),
                    collecting["line"],
                    collecting["line_end"],
                )
                if parsed:
                    pending.append(parsed)
                collecting = None
            continue

        if parameter_depth > 0:
            for item in _decorators_in_text(stripped, index):
                if _is_candidate(item["name"]):
                    rows.append(
                        _classification_row(
                            item,
                            file_path,
                            "parameter",
                            "non_route",
                            "Decorator is applied within a method parameter list.",
                        )
                    )
            parameter_depth += _paren_delta(line)
            if parameter_depth <= 0:
                parameter_depth = 0
            continue

        if stripped.startswith("@"):
            balance = _paren_delta(line)
            if balance > 0:
                collecting = {
                    "line": index,
                    "line_end": index,
                    "parts": [stripped],
                    "balance": balance,
                }
            else:
                parsed = _parse_decorator(stripped, index)
                if parsed:
                    pending.append(parsed)
            continue

        if not stripped or stripped.startswith("//"):
            continue

        context, symbol = _target_context(stripped)
        if context == "method":
            class_name = class_scopes.get(index, "")
            if not class_name:
                current_controller = None
            elif (
                not current_controller
                or current_controller.get("class_name") != class_name
            ):
                current_controller = {
                    "class_name": class_name,
                    "prefix": "",
                    "decorators": [],
                    "line": 0,
                    "controller_observed": False,
                }
        if pending:
            finish_pending(context, symbol)
        elif context == "class":
            current_controller = {
                "class_name": symbol,
                "prefix": "",
                "decorators": [],
                "line": 0,
                "controller_observed": False,
            }

        if context == "method":
            parameter_text = stripped[stripped.find("(") + 1 :]
            for item in _decorators_in_text(parameter_text, index):
                if _is_candidate(item["name"]):
                    rows.append(
                        _classification_row(
                            item,
                            file_path,
                            "parameter",
                            "non_route",
                            "Decorator is applied within a method parameter list.",
                        )
                    )
            delta = _paren_delta(line)
            if delta > 0:
                parameter_depth = delta

    if collecting is not None:
        parsed = _parse_decorator(
            " ".join(collecting["parts"]),
            collecting["line"],
            collecting["line_end"],
        )
        if parsed:
            pending.append(parsed)
    if pending:
        finish_pending("unknown")

    rows.sort(
        key=lambda row: (
            row["file"],
            row["line_start"],
            row["decorator_name"],
            row["classification_id"],
        )
    )
    routes.sort(
        key=lambda row: (
            row["method"],
            row["path"],
            row["file"],
            row["line_start"],
            row["route_id"],
        )
    )
    return {
        "classifications": rows,
        "routes": routes,
        "limitations": LIMITATIONS[:],
    }


def scan_typescript_decorators(repo_path):
    rows = []
    routes = []
    for rel, path in _iter_files(repo_path):
        result = classify_typescript_decorators(_read_lines(path), rel)
        rows.extend(result["classifications"])
        routes.extend(result["routes"])
    rows.sort(
        key=lambda row: (
            row["file"],
            row["line_start"],
            row["decorator_name"],
            row["classification_id"],
        )
    )
    routes.sort(
        key=lambda row: (
            row["method"],
            row["path"],
            row["file"],
            row["line_start"],
            row["route_id"],
        )
    )
    return {
        "version": "route_decorator_classifications_v1",
        "classifications": rows,
        "routes": routes,
        "limitations": LIMITATIONS[:],
        "summary": summarize_classifications(rows, LIMITATIONS),
    }
