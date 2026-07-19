import hashlib
import re


READ_OPERATIONS = {
    "find",
    "findBy",
    "findOne",
    "findOneBy",
    "findAndCount",
    "findAndCountBy",
    "count",
    "countBy",
    "exists",
    "existsBy",
    "preload",
    "loadRelationCountAndMap",
}
WRITE_OPERATIONS = {
    "save",
    "insert",
    "update",
    "upsert",
    "delete",
    "remove",
    "softDelete",
    "softRemove",
    "restore",
    "recover",
    "increment",
    "decrement",
    "clear",
    "persist",
    "merge",
    "flush",
}
QUERY_BUILDER_READS = {
    "getOne",
    "getOneOrFail",
    "getMany",
    "getManyAndCount",
    "getCount",
    "getRawOne",
    "getRawMany",
    "stream",
}
QUERY_BUILDER_WRITES = {"insert", "update", "delete", "softDelete", "restore"}
RECEIVER_TYPES = {
    "Repository": "repository",
    "TreeRepository": "repository",
    "MongoRepository": "repository",
    "EntityManager": "entity_manager",
    "DataSource": "data_source",
    "QueryRunner": "query_runner",
}


def _stable_id(*parts):
    raw = "|".join(str(part or "") for part in parts)
    return "typeorm-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _imported_symbols(text):
    symbols = {}
    for match in re.finditer(
        r"import\s*\{(?P<body>[^}]+)\}\s*from\s*['\"](?P<module>typeorm|@nestjs/typeorm)['\"]",
        text,
        re.MULTILINE | re.DOTALL,
    ):
        module = match.group("module")
        for item in match.group("body").split(","):
            bits = re.split(r"\s+as\s+", item.strip())
            original = bits[0].strip()
            local = bits[-1].strip()
            if original and local:
                symbols[local] = {"original": original, "module": module}
    return symbols


def _scope_map(lines):
    scopes = {}
    current = {"kind": "module", "name": ""}
    depth = 0
    method_depth = None
    method_rx = re.compile(
        r"^\s*(?:public|private|protected|static|async|readonly|\s)*"
        r"([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^;]*\)\s*(?::[^={]+)?\s*\{"
    )
    for index, line in enumerate(lines, start=1):
        match = method_rx.search(line)
        if match and match.group(1) not in {"if", "for", "while", "switch", "catch"}:
            current = {"kind": "method", "name": match.group(1)}
            method_depth = depth + line.count("{") - line.count("}")
        scopes[index] = dict(current)
        depth += line.count("{") - line.count("}")
        if method_depth is not None and depth < method_depth:
            current = {"kind": "module", "name": ""}
            method_depth = None
    return scopes


def _brace_range(lines, start_index):
    depth = 0
    opened = False
    for index in range(start_index, min(len(lines), start_index + 160)):
        line = lines[index]
        if "{" in line:
            opened = True
        depth += line.count("{") - line.count("}")
        if opened and depth <= 0:
            return start_index + 1, index + 1
    return start_index + 1, min(len(lines), start_index + 160)


def _transaction_ranges(lines, receivers):
    ranges = []
    for index, line in enumerate(lines):
        if ".transaction" not in line:
            continue
        statement = "\n".join(lines[index:min(len(lines), index + 8)])
        match = re.search(
            r"(?P<receiver>(?:this\.)?[A-Za-z_$][A-Za-z0-9_$]*)"
            r"\.transaction\s*\(\s*(?:async\s*)?\(?\s*(?P<manager>[A-Za-z_$][A-Za-z0-9_$]*)",
            statement,
            re.DOTALL,
        )
        if not match:
            continue
        receiver_name = match.group("receiver").removeprefix("this.")
        receiver = receivers.get(receiver_name)
        if not receiver or receiver["kind"] not in {"data_source", "entity_manager"}:
            continue
        start, end = _brace_range(lines, index)
        manager = match.group("manager")
        ranges.append({"start": start, "end": end, "manager": manager})
        receivers.setdefault(
            manager,
            {"kind": "entity_manager", "entity": "", "source": "transaction_callback"},
        )
    return ranges


def _query_runner_ranges(lines, receivers):
    ranges = []
    active = {}
    for index, line in enumerate(lines, start=1):
        for name, receiver in receivers.items():
            if receiver["kind"] != "query_runner":
                continue
            token = rf"(?:this\.)?{re.escape(name)}"
            if re.search(token + r"\.startTransaction\s*\(", line):
                active[name] = index
            if re.search(token + r"\.(?:commitTransaction|rollbackTransaction)\s*\(", line):
                start = active.pop(name, None)
                if start:
                    ranges.append({"start": start, "end": index, "runner": name})
    return ranges


def _transaction_context(line, receiver_name, callback_ranges, runner_ranges):
    for item in callback_ranges:
        if item["start"] <= line <= item["end"]:
            return "explicit_callback"
    for item in runner_ranges:
        if item["start"] <= line <= item["end"]:
            return "query_runner_explicit"
    return "unknown"


def _first_argument(call_text):
    match = re.search(r"\(\s*(.+)", call_text, re.DOTALL)
    if not match:
        return ""
    value = match.group(1).strip()
    quote = value[:1]
    if quote in {"'", '"', "`"}:
        escaped = False
        out = []
        for char in value[1:]:
            if char == quote and not escaped:
                return "".join(out)
            out.append(char)
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
    return value.split(",", 1)[0].split(")", 1)[0].strip()


def _raw_sql_kind(sql):
    value = str(sql or "").strip()
    if not value or "${" in value:
        return "db.query_unknown"
    cleaned = re.sub(r"^(?:--[^\n]*\n|/\*.*?\*/\s*)+", "", value, flags=re.DOTALL).strip()
    keyword = (re.match(r"([A-Za-z]+)", cleaned) or [None, ""])[1].upper()
    if keyword == "SELECT":
        return "db.read"
    if keyword == "WITH":
        return "db.read" if re.search(r"\bSELECT\b", cleaned, re.IGNORECASE) else "db.query_unknown"
    if keyword in {"INSERT", "UPDATE", "DELETE", "MERGE", "REPLACE", "TRUNCATE", "CREATE", "ALTER", "DROP"}:
        return "db.write"
    return "db.query_unknown"


def _operation(
    kind,
    operation,
    receiver_kind,
    receiver_name,
    entity,
    line,
    scope,
    transaction_context="unknown",
    confidence=0.9,
    signals=None,
    limitations=None,
):
    return {
        "operation_id": _stable_id(kind, operation, receiver_kind, receiver_name, entity, line),
        "kind": kind,
        "operation": operation,
        "receiver_kind": receiver_kind,
        "receiver_name": receiver_name,
        "entity": entity or "",
        "line_start": int(line),
        "line_end": int(line),
        "scope": scope or {"kind": "module", "name": ""},
        "transaction_context": transaction_context,
        "confidence": float(confidence),
        "signals": sorted(set(signals or [])),
        "limitations": sorted(set(limitations or [])),
    }


def _collect_receivers(lines, symbols):
    text = "\n".join(lines)
    receivers = {}
    allowed_types = {
        local: RECEIVER_TYPES[info["original"]]
        for local, info in symbols.items()
        if info["original"] in RECEIVER_TYPES
    }
    type_names = "|".join(re.escape(name) for name in allowed_types)
    if type_names:
        rx = re.compile(
            rf"\b(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*:\s*"
            rf"(?P<type>{type_names})(?:\s*<\s*(?P<entity>[A-Za-z_$][A-Za-z0-9_$.]*)\s*>)?"
        )
        for match in rx.finditer(text):
            receivers[match.group("name")] = {
                "kind": allowed_types[match.group("type")],
                "entity": match.group("entity") or "",
                "source": "typeorm_type",
            }
    for match in re.finditer(
        r"@InjectRepository\s*\(\s*(?P<entity>[A-Za-z_$][A-Za-z0-9_$.]*)[^)]*\)"
        r"[\s\S]{0,240}?"
        r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*:\s*"
        r"(?:Repository|TreeRepository|MongoRepository)(?:\s*<[^>]+>)?",
        text,
    ):
        receivers[match.group("name")] = {
            "kind": "repository",
            "entity": match.group("entity"),
            "source": "inject_repository",
        }
    get_repo_rx = re.compile(
        r"(?:const|let|var)\s+(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*="
        r"\s*(?P<owner>(?:this\.)?[A-Za-z_$][A-Za-z0-9_$.]*)"
        r"\.getRepository\s*\(\s*(?P<entity>[A-Za-z_$][A-Za-z0-9_$.]*)"
    )
    for match in get_repo_rx.finditer(text):
        owner = match.group("owner").split(".")[-1]
        if owner in receivers or any(
            receivers.get(part, {}).get("kind") in {"data_source", "entity_manager"}
            for part in match.group("owner").split(".")
        ):
            receivers[match.group("name")] = {
                "kind": "repository",
                "entity": match.group("entity"),
                "source": "get_repository",
            }
    runner_rx = re.compile(
        r"(?:const|let|var)\s+(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*="
        r"\s*(?P<owner>(?:this\.)?[A-Za-z_$][A-Za-z0-9_$.]*)\.createQueryRunner\s*\("
    )
    for match in runner_rx.finditer(text):
        owner = match.group("owner").split(".")[-1]
        if receivers.get(owner, {}).get("kind") == "data_source":
            receivers[match.group("name")] = {
                "kind": "query_runner",
                "entity": "",
                "source": "create_query_runner",
            }
    return receivers


def detect_typeorm_operations(lines):
    text = "\n".join(lines)
    symbols = _imported_symbols(text)
    if not any(info["module"] in {"typeorm", "@nestjs/typeorm"} for info in symbols.values()):
        return []
    scopes = _scope_map(lines)
    receivers = _collect_receivers(lines, symbols)
    callback_ranges = _transaction_ranges(lines, receivers)
    runner_ranges = _query_runner_ranges(lines, receivers)
    base_entity_aliases = {
        local for local, info in symbols.items() if info["original"] == "BaseEntity"
    }
    base_entities = set()
    if base_entity_aliases:
        aliases = "|".join(re.escape(name) for name in base_entity_aliases)
        for match in re.finditer(
            rf"\bclass\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+extends\s+(?:{aliases})\b",
            text,
        ):
            base_entities.add(match.group(1))

    operations = []
    for index, line in enumerate(lines, start=1):
        scope = scopes.get(index)
        callback_repository = re.search(
            r"(?<![\w$.])(?P<manager>[A-Za-z_$][A-Za-z0-9_$]*)"
            r"\.getRepository\s*\(\s*(?P<entity>[A-Za-z_$][A-Za-z0-9_$.]*)\s*\)"
            r"\.(?P<op>[A-Za-z_$][A-Za-z0-9_$]*)\s*\(",
            line,
        )
        if (
            callback_repository
            and receivers.get(callback_repository.group("manager"), {}).get("source")
            == "transaction_callback"
        ):
            op = callback_repository.group("op")
            if op in READ_OPERATIONS | WRITE_OPERATIONS:
                operations.append(
                    _operation(
                        "db.read" if op in READ_OPERATIONS else "db.write",
                        op,
                        "repository",
                        callback_repository.group("manager") + ".getRepository",
                        callback_repository.group("entity"),
                        index,
                        scope,
                        "explicit_callback",
                        confidence=0.95,
                        signals=["transaction_callback", "get_repository"],
                    )
                )
        for name, receiver in list(receivers.items()):
            receiver_match = re.search(
                rf"(?<![\w$.])(?P<alias>(?:this\.)?{re.escape(name)})"
                r"\.(?P<op>[A-Za-z_$][A-Za-z0-9_$]*)\s*\(",
                line,
            )
            manager_match = re.search(
                rf"(?<![\w$.])(?P<alias>(?:this\.)?{re.escape(name)}\.manager)"
                r"\.(?P<op>[A-Za-z_$][A-Za-z0-9_$]*)\s*\(",
                line,
            )
            matches = []
            if receiver_match:
                matches.append((receiver_match, receiver["kind"]))
            if (
                manager_match
                and receiver["kind"] in {"data_source", "query_runner"}
            ):
                nested_kind = (
                    "query_runner"
                    if receiver["kind"] == "query_runner"
                    else "entity_manager"
                )
                matches.append((manager_match, nested_kind))
            for match, effective_receiver_kind in matches:
                alias = match.group("alias")
                op = match.group("op")
                kind = None
                limitations = []
                signals = [receiver.get("source") or "typeorm_receiver"]
                if op in READ_OPERATIONS:
                    kind = "db.read"
                elif op in WRITE_OPERATIONS:
                    kind = "db.write"
                    if op == "merge":
                        limitations.append("persistence_effect_requires_confirmation")
                        signals.append("write_intent")
                elif op == "query":
                    call_text = "\n".join(
                        [line[match.start():]]
                        + lines[index:min(len(lines), index + 80)]
                    )
                    sql = _first_argument(call_text)
                    kind = _raw_sql_kind(sql)
                    if kind == "db.query_unknown":
                        limitations.append("dynamic_sql_operation_unresolved")
                    else:
                        signals.append("static_sql")
                elif op in {"startTransaction", "commitTransaction", "rollbackTransaction", "transaction"}:
                    kind = "db.transaction"
                if not kind:
                    continue
                tx_context = _transaction_context(index, name, callback_ranges, runner_ranges)
                entity = receiver.get("entity") or ""
                operations.append(
                    _operation(
                        kind,
                        op,
                        effective_receiver_kind,
                        alias,
                        entity,
                        index,
                        scope,
                        tx_context,
                        confidence=0.94 if receiver.get("source") == "inject_repository" else 0.9,
                        signals=signals,
                        limitations=limitations,
                    )
                )

        for entity in base_entities:
            match = re.search(
                rf"\b{re.escape(entity)}\.(?P<op>{'|'.join(sorted(READ_OPERATIONS | WRITE_OPERATIONS))})\s*\(",
                line,
            )
            if match:
                op = match.group("op")
                operations.append(
                    _operation(
                        "db.read" if op in READ_OPERATIONS else "db.write",
                        op,
                        "base_entity",
                        entity,
                        entity,
                        index,
                        scope,
                        _transaction_context(index, entity, callback_ranges, runner_ranges),
                        confidence=0.9,
                        signals=["typeorm_base_entity"],
                    )
                )

    # QueryBuilder chains are classified only when their origin is a confirmed TypeORM receiver.
    for start in range(len(lines)):
        statement = "\n".join(lines[start:min(len(lines), start + 20)])
        end_at = statement.find(";")
        if end_at >= 0:
            statement = statement[: end_at + 1]
        origin = re.search(
            r"(?P<receiver>(?:this\.)?[A-Za-z_$][A-Za-z0-9_$]*)\.createQueryBuilder\s*\(",
            statement,
        )
        if not origin:
            continue
        receiver_name = origin.group("receiver").removeprefix("this.")
        receiver = receivers.get(receiver_name)
        if not receiver or receiver["kind"] not in {"repository", "entity_manager", "data_source", "query_runner"}:
            continue
        calls = re.findall(r"\.([A-Za-z_$][A-Za-z0-9_$]*)\s*\(", statement)
        read = next((op for op in calls if op in QUERY_BUILDER_READS), None)
        write = next((op for op in calls if op in QUERY_BUILDER_WRITES), None)
        relation_write = "relation" in calls and next((op for op in calls if op in {"add", "remove", "set"}), None)
        execute = "execute" in calls
        line = start + 1
        if read:
            operations.append(
                _operation(
                    "db.read", read, "query_builder", origin.group("receiver"),
                    receiver.get("entity"), line, scopes.get(line),
                    _transaction_context(line, receiver_name, callback_ranges, runner_ranges),
                    confidence=0.91, signals=["typeorm_query_builder"],
                )
            )
        elif write and execute:
            operations.append(
                _operation(
                    "db.write", write, "query_builder", origin.group("receiver"),
                    receiver.get("entity"), line, scopes.get(line),
                    _transaction_context(line, receiver_name, callback_ranges, runner_ranges),
                    confidence=0.92, signals=["typeorm_query_builder", "execute_terminal"],
                )
            )
        elif relation_write:
            operations.append(
                _operation(
                    "db.write", f"relation.{relation_write}", "query_builder",
                    origin.group("receiver"), receiver.get("entity"), line, scopes.get(line),
                    _transaction_context(line, receiver_name, callback_ranges, runner_ranges),
                    confidence=0.9, signals=["typeorm_query_builder", "relation_mutation"],
                )
            )

    unique = {}
    for item in operations:
        key = (
            item["kind"],
            item["operation"],
            item["receiver_kind"],
            item["receiver_name"],
            item["line_start"],
        )
        unique.setdefault(key, item)
    return sorted(
        unique.values(),
        key=lambda item: (
            item["line_start"],
            item["kind"],
            item["receiver_name"],
            item["operation"],
        ),
    )


def detect_typeorm_transactions(lines):
    return [
        item
        for item in detect_typeorm_operations(lines)
        if item["kind"] == "db.transaction"
    ]
