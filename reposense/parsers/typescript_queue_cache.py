import re


QUEUE_PACKAGES = {"bull", "bullmq"}
REDIS_PACKAGES = {"redis", "ioredis"}
CACHE_READ_OPS = {"get", "mget", "hget"}
CACHE_WRITE_OPS = {"set", "setex", "hset", "expire"}
CACHE_INVALIDATE_OPS = {"del", "unlink", "hdel"}


def _first_arg_expression(call_text):
    value = str(call_text or "")
    start = value.find("(")
    if start < 0:
        return ""
    quote = ""
    escaped = False
    depth = 0
    out = []
    for char in value[start + 1 :]:
        if quote:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            continue
        if char in {"'", '"', "`"}:
            quote = char
            out.append(char)
        elif char in "([{":
            depth += 1
            out.append(char)
        elif char in ")]}":
            if char == ")" and depth == 0:
                break
            depth = max(0, depth - 1)
            out.append(char)
        elif char == "," and depth == 0:
            break
        else:
            out.append(char)
    return "".join(out).strip()


def _string_constants(lines):
    constants = {}
    pattern = re.compile(
        r"\bconst\s+([A-Za-z_$][A-Za-z0-9_$]*)"
        r"(?:\s*:\s*string)?\s*=\s*(['\"])(.*?)\2"
    )
    for line in lines:
        match = pattern.search(line)
        if match:
            constants[match.group(1)] = match.group(3)
    return constants


def _resolve_name(expression, constants):
    expr = str(expression or "").strip()
    literal = re.fullmatch(r"(['\"])(.*?)\1", expr, re.S)
    if literal:
        return literal.group(2), expr, True
    if expr in constants:
        return constants[expr], expr, True
    return "", expr[:300], False


def _named_imports(text, package):
    aliases = {}
    pattern = re.compile(
        rf"import\s*\{{([^}}]*)\}}\s*from\s*['\"]{re.escape(package)}['\"]",
        re.S,
    )
    for match in pattern.finditer(text):
        for part in match.group(1).split(","):
            item = part.strip()
            alias_match = re.fullmatch(
                r"([A-Za-z_$][A-Za-z0-9_$]*)"
                r"(?:\s+as\s+([A-Za-z_$][A-Za-z0-9_$]*))?",
                item,
            )
            if alias_match:
                aliases[alias_match.group(2) or alias_match.group(1)] = (
                    alias_match.group(1)
                )
    return aliases


def _default_imports(text, package):
    return {
        match.group(1)
        for match in re.finditer(
            rf"import\s+([A-Za-z_$][A-Za-z0-9_$]*)"
            rf"\s*(?:,\s*\{{[^}}]*\}})?\s*from\s*['\"]{re.escape(package)}['\"]",
            text,
            re.S,
        )
    }


def _require_imports(text, package):
    aliases = {}
    pattern = re.compile(
        rf"(?:const|let|var)\s*\{{([^}}]*)\}}\s*=\s*require\(\s*['\"]"
        rf"{re.escape(package)}['\"]\s*\)",
        re.S,
    )
    for match in pattern.finditer(text):
        for part in match.group(1).split(","):
            item = part.strip()
            alias_match = re.fullmatch(
                r"([A-Za-z_$][A-Za-z0-9_$]*)"
                r"(?:\s*:\s*([A-Za-z_$][A-Za-z0-9_$]*))?",
                item,
            )
            if alias_match:
                aliases[alias_match.group(2) or alias_match.group(1)] = (
                    alias_match.group(1)
                )
    return aliases


def _queue_symbols(lines):
    text = "\n".join(lines)
    queue_ctors = {}
    worker_ctors = {}
    for package in QUEUE_PACKAGES:
        framework = "bullmq" if package == "bullmq" else "bull"
        aliases = _named_imports(text, package)
        aliases.update(_require_imports(text, package))
        for alias, original in aliases.items():
            if original == "Queue":
                queue_ctors[alias] = framework
            elif original == "Worker":
                worker_ctors[alias] = framework
        for alias in _default_imports(text, package):
            if package == "bull":
                queue_ctors[alias] = framework
    if "bullmq" in text.lower():
        queue_ctors.setdefault("Queue", "bullmq")
        worker_ctors.setdefault("Worker", "bullmq")
    if re.search(r"\bnew\s+Worker(?:\s*<[^;()]+>)?\s*\(", text):
        worker_ctors.setdefault("Worker", "bullmq")
    if re.search(r"from\s*['\"]bull['\"]|require\(\s*['\"]bull['\"]", text):
        queue_ctors.setdefault("Queue", "bull")
    return queue_ctors, worker_ctors


def _nest_queue_symbols(lines):
    text = "\n".join(lines)
    symbols = {
        "bullmq": {"InjectQueue": set(), "Processor": set(), "WorkerHost": set()},
        "bull": {"InjectQueue": set(), "Processor": set(), "WorkerHost": set()},
    }
    for package, framework in (
        ("@nestjs/bullmq", "bullmq"),
        ("@nestjs/bull", "bull"),
    ):
        aliases = _named_imports(text, package)
        aliases.update(_require_imports(text, package))
        for alias, original in aliases.items():
            if original in symbols[framework]:
                symbols[framework][original].add(alias)
    return symbols


def _nest_queue_instances(lines, constants, symbols):
    instances = {}
    for line_number, line in enumerate(lines):
        for framework, names in symbols.items():
            for decorator in names["InjectQueue"]:
                match = re.search(
                    rf"@{re.escape(decorator)}\s*\(",
                    line,
                )
                if not match:
                    continue
                expression = _first_arg_expression(line[match.end() - 1 :])
                target_text = line[match.end() :]
                if not re.search(
                    r"\b(?:private|protected|public|readonly)\b",
                    target_text,
                ):
                    target_text = " ".join(
                        lines[line_number + 1 : line_number + 4]
                    )
                field = re.search(
                    r"\b(?:private|protected|public)?\s*(?:readonly\s+)?"
                    r"([A-Za-z_$][A-Za-z0-9_$]*)\s*[!?]?\s*:\s*"
                    r"[A-Za-z_$][A-Za-z0-9_$]*",
                    target_text,
                )
                if not field:
                    continue
                name, raw, resolved = _resolve_name(expression, constants)
                instances[field.group(1)] = {
                    "framework": framework,
                    "queue_name": name,
                    "queue_name_expr": raw,
                    "queue_name_resolved": resolved,
                }
    return instances


def _nest_queue_symbols(lines):
    text = "\n".join(lines)
    symbols = {
        "bullmq": {"InjectQueue": set(), "Processor": set(), "WorkerHost": set()},
        "bull": {"InjectQueue": set(), "Processor": set(), "WorkerHost": set()},
    }
    for package, framework in (
        ("@nestjs/bullmq", "bullmq"),
        ("@nestjs/bull", "bull"),
    ):
        aliases = _named_imports(text, package)
        aliases.update(_require_imports(text, package))
        for alias, original in aliases.items():
            if original in symbols[framework]:
                symbols[framework][original].add(alias)
    return symbols


def _nest_queue_instances(lines, constants, symbols):
    instances = {}
    for line_number, line in enumerate(lines):
        for framework, names in symbols.items():
            for decorator in names["InjectQueue"]:
                match = re.search(
                    rf"@{re.escape(decorator)}\s*\(",
                    line,
                )
                if not match:
                    continue
                expression = _first_arg_expression(line[match.end() - 1 :])
                target_text = line[match.end() :]
                if not re.search(
                    r"\b(?:private|protected|public|readonly)\b",
                    target_text,
                ):
                    target_text = " ".join(
                        lines[line_number + 1 : line_number + 4]
                    )
                field = re.search(
                    r"\b(?:private|protected|public)?\s*(?:readonly\s+)?"
                    r"([A-Za-z_$][A-Za-z0-9_$]*)\s*[!?]?\s*:\s*"
                    r"[A-Za-z_$][A-Za-z0-9_$]*",
                    target_text,
                )
                if not field:
                    continue
                name, raw, resolved = _resolve_name(expression, constants)
                instances[field.group(1)] = {
                    "framework": framework,
                    "queue_name": name,
                    "queue_name_expr": raw,
                    "queue_name_resolved": resolved,
                }
    return instances


def _queue_instances(lines, constants, queue_ctors):
    instances = {}
    constructor = re.compile(
        r"\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)"
        r"\s*=\s*new\s+([A-Za-z_$][A-Za-z0-9_$]*)"
        r"(?:\s*<[^;()]+>)?\s*\("
    )
    for line in lines:
        match = constructor.search(line)
        if not match or match.group(2) not in queue_ctors:
            continue
        expression = _first_arg_expression(line[match.end() - 1 :])
        name, raw, resolved = _resolve_name(expression, constants)
        instances[match.group(1)] = {
            "framework": queue_ctors[match.group(2)],
            "queue_name": name,
            "queue_name_expr": raw,
            "queue_name_resolved": resolved,
        }
    return instances


def _receiver_binding(receiver, bindings):
    direct = bindings.get(receiver)
    if direct:
        return direct
    return bindings.get(receiver.split(".")[-1])


def detect_ts_queue_dispatch(lines):
    out = []
    constants = _string_constants(lines)
    queue_ctors, _worker_ctors = _queue_symbols(lines)
    instances = _queue_instances(lines, constants, queue_ctors)
    instances.update(
        _nest_queue_instances(
            lines,
            constants,
            _nest_queue_symbols(lines),
        )
    )
    instances.update(
        _nest_queue_instances(
            lines,
            constants,
            _nest_queue_symbols(lines),
        )
    )
    pattern = re.compile(
        r"([A-Za-z_$][A-Za-z0-9_$.]*)\.add\s*(?:<[^;()]+>)?\s*\("
    )
    seen = set()
    for line_number, line in enumerate(lines, 1):
        for match in pattern.finditer(line):
            receiver = match.group(1)
            binding = _receiver_binding(receiver, instances)
            receiver_hint = receiver.lower()
            if not binding and not any(
                token in receiver_hint for token in ("queue", "bull")
            ):
                continue
            job_expr = _first_arg_expression(line[match.end() - 1 :])
            job_name, _job_raw, _job_resolved = _resolve_name(
                job_expr,
                constants,
            )
            binding = binding or {
                "framework": (
                    "bull"
                    if "bull" in receiver_hint and "bullmq" not in receiver_hint
                    else "bullmq"
                ),
                "queue_name": "",
                "queue_name_expr": "",
                "queue_name_resolved": False,
            }
            key = (
                line_number,
                receiver,
                binding["framework"],
                binding["queue_name"],
                job_name,
            )
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    **binding,
                    "job_name": job_name,
                    "callee_expr": receiver + ".add",
                    "start_line": line_number,
                    "end_line": line_number,
                    "parse_level": "L2",
                }
            )
    return out


def detect_ts_queue_consume(lines):
    out = []
    constants = _string_constants(lines)
    queue_ctors, worker_ctors = _queue_symbols(lines)
    instances = _queue_instances(lines, constants, queue_ctors)
    nest_symbols = _nest_queue_symbols(lines)
    worker_names = "|".join(
        re.escape(name)
        for name in sorted(worker_ctors, key=len, reverse=True)
    )
    seen = set()
    if worker_names:
        worker_pattern = re.compile(
            rf"\bnew\s+({worker_names})(?:\s*<[^;()]+>)?\s*\("
        )
        for line_number, line in enumerate(lines, 1):
            for match in worker_pattern.finditer(line):
                expression = _first_arg_expression(line[match.end() - 1 :])
                name, raw, resolved = _resolve_name(expression, constants)
                framework = worker_ctors[match.group(1)]
                key = (line_number, framework, name, raw, "worker")
                if key in seen:
                    continue
                seen.add(key)
                out.append(
                    {
                        "framework": framework,
                        "queue_name": name,
                        "queue_name_expr": raw,
                        "queue_name_resolved": resolved,
                        "job_name": "",
                        "consumer_style": "worker",
                        "callee_expr": "new " + match.group(1),
                        "start_line": line_number,
                        "end_line": line_number,
                        "parse_level": "L2",
                    }
                )
    for line_number, line in enumerate(lines, 1):
        for framework, names in nest_symbols.items():
            for decorator in names["Processor"]:
                match = re.search(
                    rf"@{re.escape(decorator)}\s*\(",
                    line,
                )
                if not match:
                    continue
                following = " ".join(
                    lines[line_number : line_number + 8]
                )
                worker_hosts = names["WorkerHost"]
                if worker_hosts and not any(
                    re.search(
                        rf"\bextends\s+{re.escape(host)}\b",
                        following,
                    )
                    for host in worker_hosts
                ):
                    continue
                expression = _first_arg_expression(line[match.end() - 1 :])
                name, raw, resolved = _resolve_name(expression, constants)
                key = (
                    line_number,
                    framework,
                    name,
                    raw,
                    "nest_processor",
                )
                if key in seen:
                    continue
                seen.add(key)
                out.append(
                    {
                        "framework": framework,
                        "queue_name": name,
                        "queue_name_expr": raw,
                        "queue_name_resolved": resolved,
                        "job_name": "",
                        "consumer_style": "nest_processor",
                        "callee_expr": "@" + decorator,
                        "start_line": line_number,
                        "end_line": line_number,
                        "parse_level": "L2",
                    }
                )
    process_pattern = re.compile(
        r"([A-Za-z_$][A-Za-z0-9_$.]*)\.process\s*\("
    )
    for line_number, line in enumerate(lines, 1):
        for match in process_pattern.finditer(line):
            receiver = match.group(1)
            binding = _receiver_binding(receiver, instances)
            if not binding and not any(
                token in receiver.lower() for token in ("queue", "bull")
            ):
                continue
            binding = binding or {
                "framework": "bull",
                "queue_name": "",
                "queue_name_expr": "",
                "queue_name_resolved": False,
            }
            key = (
                line_number,
                binding["framework"],
                binding["queue_name"],
                binding["queue_name_expr"],
                "process",
            )
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    **binding,
                    "job_name": "",
                    "consumer_style": "process",
                    "callee_expr": receiver + ".process",
                    "start_line": line_number,
                    "end_line": line_number,
                    "parse_level": "L2",
                }
            )
    out.sort(
        key=lambda item: (
            item["start_line"],
            item["framework"],
            item["queue_name"],
            item["callee_expr"],
        )
    )
    return out


def _redis_symbols(lines):
    text = "\n".join(lines)
    constructors = {}
    factories = {}
    for package in REDIS_PACKAGES:
        aliases = _named_imports(text, package)
        aliases.update(_require_imports(text, package))
        for alias, original in aliases.items():
            if original in {"Redis", "Cluster"}:
                constructors[alias] = package
            elif original == "createClient":
                factories[alias] = package
        for alias in _default_imports(text, package):
            constructors[alias] = package
    if "ioredis" in text.lower():
        constructors.setdefault("Redis", "ioredis")
    if re.search(r"from\s*['\"]redis['\"]|require\(\s*['\"]redis['\"]", text):
        factories.setdefault("createClient", "redis")
    return constructors, factories


def _redis_clients(lines, constructors, factories):
    clients = {}
    constructor_names = "|".join(
        re.escape(name)
        for name in sorted(constructors, key=len, reverse=True)
    )
    factory_names = "|".join(
        re.escape(name)
        for name in sorted(factories, key=len, reverse=True)
    )
    for line in lines:
        if constructor_names:
            match = re.search(
                rf"\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)"
                rf"\s*=\s*new\s+({constructor_names})(?:\s*<[^;()]+>)?\s*\(",
                line,
            )
            if match:
                clients[match.group(1)] = constructors[match.group(2)]
        if factory_names:
            match = re.search(
                rf"\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)"
                rf"\s*=\s*({factory_names})\s*\(",
                line,
            )
            if match:
                clients[match.group(1)] = factories[match.group(2)]
        typed = re.search(
            r"\b(?:private|protected|public)?\s*(?:readonly\s+)?"
            r"([A-Za-z_$][A-Za-z0-9_$]*)\s*[!?]?\s*:\s*"
            r"([A-Za-z_$][A-Za-z0-9_$]*)\b",
            line,
        )
        if typed and typed.group(2) in constructors:
            clients[typed.group(1)] = constructors[typed.group(2)]
    for line in lines:
        pipeline = re.search(
            r"\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)"
            r"\s*=\s*([A-Za-z_$][A-Za-z0-9_$.]*)\.(?:pipeline|multi)\s*\(",
            line,
        )
        if not pipeline:
            continue
        source = pipeline.group(2)
        source_kind = clients.get(source) or clients.get(source.split(".")[-1])
        if source_kind:
            clients[pipeline.group(1)] = source_kind
    return clients


def _cache_receiver(receiver, clients):
    framework = clients.get(receiver) or clients.get(receiver.split(".")[-1])
    if framework:
        return framework, "resolved_client"
    lowered = receiver.lower()
    segments = lowered.split(".")
    if any(
        segment == "redis"
        or segment.endswith("redisclient")
        or segment.endswith("redisservice")
        or segment.endswith("redisconnection")
        for segment in segments
    ):
        return "ioredis", "receiver_name"
    if any(
        segment == "cache"
        or segment.endswith("cacheservice")
        or segment.endswith("cacheclient")
        or segment.endswith("cachestore")
        for segment in segments
    ):
        return "redis", "wrapper_receiver"
    return "", ""


def detect_ts_cache_ops(lines):
    out = []
    constants = _string_constants(lines)
    constructors, factories = _redis_symbols(lines)
    clients = _redis_clients(lines, constructors, factories)
    operations = sorted(
        CACHE_READ_OPS | CACHE_WRITE_OPS | CACHE_INVALIDATE_OPS,
        key=len,
        reverse=True,
    )
    pattern = re.compile(
        r"([A-Za-z_$][A-Za-z0-9_$.]*)\.("
        + "|".join(re.escape(op) for op in operations)
        + r")\s*\("
    )
    seen = set()
    for line_number, line in enumerate(lines, 1):
        for match in pattern.finditer(line):
            receiver = match.group(1)
            operation = match.group(2)
            framework, receiver_source = _cache_receiver(receiver, clients)
            if not framework:
                continue
            call_text = line[match.end() - 1 :]
            if not _first_arg_expression(call_text):
                call_text = call_text + "\n" + "\n".join(
                    lines[line_number : line_number + 5]
                )
            expression = _first_arg_expression(call_text)
            key_literal, key_expression, resolved = _resolve_name(
                expression,
                constants,
            )
            if operation in CACHE_READ_OPS:
                event_kind = "cache.read"
            elif operation in CACHE_WRITE_OPS:
                event_kind = "cache.write"
            else:
                event_kind = "cache.invalidate"
            signature = (
                line_number,
                receiver,
                operation,
                key_expression,
            )
            if signature in seen:
                continue
            seen.add(signature)
            out.append(
                {
                    "framework": framework,
                    "cache_op": operation,
                    "event_kind": event_kind,
                    "key_literal": key_literal,
                    "key_expr": key_expression,
                    "key_resolved": resolved,
                    "callee_expr": receiver + "." + operation,
                    "receiver_source": receiver_source,
                    "start_line": line_number,
                    "end_line": line_number,
                    "parse_level": "L2",
                }
            )
    return out
