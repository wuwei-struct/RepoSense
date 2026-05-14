import re


_VERBS = {"GET", "POST", "PUT", "DELETE", "PATCH"}


def _norm_path(p):
    s = str(p or "").strip()
    if not s:
        return "/"
    s = s.replace("\\", "/")
    while "//" in s:
        s = s.replace("//", "/")
    if not s.startswith("/"):
        s = "/" + s
    if len(s) > 1 and s.endswith("/"):
        s = s[:-1]
    return s


def _join_path(a, b):
    aa = _norm_path(a)
    bb = _norm_path(b)
    if bb == "/":
        return aa
    if aa == "/":
        return bb
    return _norm_path(aa + "/" + bb.lstrip("/"))


def detect_ts_express_routes(lines):
    out = []
    router_prefix = {}
    rx_use = re.compile(r"\bapp\.use\s*\(\s*(['\"])([^'\"]+)\1\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)")
    for line in lines:
        mu = rx_use.search(line)
        if mu:
            router_prefix[mu.group(3)] = _norm_path(mu.group(2))
    rx = re.compile(r"\b(app|router)\.(get|post|put|delete|patch)\s*\(\s*(['\"])([^'\"]+)\3")
    for i, line in enumerate(lines, start=1):
        m = rx.search(line)
        if not m:
            continue
        method = m.group(2).upper()
        path = m.group(4)
        if method not in _VERBS or not path:
            continue
        sym = m.group(1)
        rp = ""
        if sym == "router":
            rp = router_prefix.get("router") or ""
        path_out = _join_path(rp, _norm_path(path)) if rp else _norm_path(path)
        out.append(
            {
                "framework": "express",
                "method": method,
                "path": path_out,
                "start_line": i,
                "end_line": i,
                "symbol": sym,
                "parse_level": "L2",
            }
        )
    return out


def detect_ts_nest_routes(lines):
    out = []
    rx_ctrl = re.compile(r"@Controller\s*\(\s*(?:(['\"])([^'\"]*)\1)?\s*\)")
    rx_verb = re.compile(r"@(Get|Post|Put|Delete|Patch)\s*\(\s*(?:(['\"])([^'\"]*)\2)?\s*\)")
    rx_method = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")
    pending_prefix = None
    current_prefix = None
    class_depth = 0
    for i, line in enumerate(lines, start=1):
        mc = rx_ctrl.search(line)
        if mc:
            pending_prefix = mc.group(2) or ""
        if pending_prefix is not None and "class " in line and "{" in line:
            current_prefix = pending_prefix
            pending_prefix = None
            class_depth = line.count("{") - line.count("}")
            if class_depth <= 0:
                class_depth = 1
            continue
        if class_depth > 0:
            class_depth += line.count("{") - line.count("}")
            if class_depth <= 0:
                current_prefix = None
                class_depth = 0
        mv = rx_verb.search(line)
        if not mv or current_prefix is None:
            continue
        method = mv.group(1).upper()
        mpath = mv.group(3) or ""
        symbol = ""
        for j in range(i, min(i + 6, len(lines))):
            nx = lines[j].strip()
            if not nx or nx.startswith("@"):
                continue
            mm = rx_method.search(nx)
            if mm:
                symbol = mm.group(1)
            break
        out.append(
            {
                "framework": "nestjs",
                "method": method,
                "path": _join_path(current_prefix, mpath),
                "start_line": i,
                "end_line": i,
                "symbol": symbol,
                "controller_prefix": _norm_path(current_prefix),
                "parse_level": "L2",
            }
        )
    return out


def detect_ts_prisma_transactions(lines):
    out = []
    rx = re.compile(r"([A-Za-z0-9_$.]+)\.\$transaction\s*\(")
    for i, line in enumerate(lines, start=1):
        m = rx.search(line)
        if not m:
            continue
        callee = m.group(1) + ".$transaction"
        out.append(
            {
                "framework": "prisma",
                "transaction_style": "prisma.$transaction",
                "callee_expr": callee,
                "start_line": i,
                "end_line": i,
                "parse_level": "L2",
            }
        )
    return out


def detect_ts_typeorm_transactions(lines):
    out = []
    rx = re.compile(r"([A-Za-z0-9_$.]+)\.transaction\s*\(")
    for i, line in enumerate(lines, start=1):
        m = rx.search(line)
        if not m:
            continue
        callee_base = m.group(1)
        lb = callee_base.lower()
        if not any(x in lb for x in ["datasource", "manager", "connection"]):
            continue
        out.append(
            {
                "framework": "typeorm",
                "transaction_style": "typeorm.transaction",
                "callee_expr": callee_base + ".transaction",
                "start_line": i,
                "end_line": i,
                "parse_level": "L2",
            }
        )
    return out


def _extract_literal_arg(call_text):
    m = re.search(r"\(\s*(['\"])([^'\"]+)\1", call_text or "")
    if not m:
        return ""
    return m.group(2)


def detect_ts_queue_dispatch(lines):
    out = []
    rx_add = re.compile(r"([A-Za-z0-9_$.]+)\.add\s*\(")
    for i, line in enumerate(lines, start=1):
        m = rx_add.search(line)
        if not m:
            continue
        callee_base = m.group(1)
        lb = callee_base.lower()
        if not any(x in lb for x in ["queue", "bull"]):
            continue
        queue_name = ""
        job_name = _extract_literal_arg(line)
        framework = "bullmq"
        if "bullmq" not in lb and "bull" in lb:
            framework = "bull"
        out.append(
            {
                "framework": framework,
                "queue_name": queue_name,
                "job_name": job_name,
                "callee_expr": callee_base + ".add",
                "start_line": i,
                "end_line": i,
                "parse_level": "L2",
            }
        )
    return out


def detect_ts_queue_consume(lines):
    out = []
    rx_worker = re.compile(r"new\s+Worker\s*\(\s*(['\"])([^'\"]+)\1")
    rx_process = re.compile(r"([A-Za-z0-9_$.]+)\.process\s*\(")
    for i, line in enumerate(lines, start=1):
        m = rx_worker.search(line)
        if m:
            out.append(
                {
                    "framework": "bullmq",
                    "queue_name": m.group(2),
                    "job_name": "",
                    "consumer_style": "worker",
                    "callee_expr": "new Worker",
                    "start_line": i,
                    "end_line": i,
                    "parse_level": "L2",
                }
            )
        m2 = rx_process.search(line)
        if m2:
            callee_base = m2.group(1)
            lb = callee_base.lower()
            if any(x in lb for x in ["queue", "bull"]):
                out.append(
                    {
                        "framework": "bull",
                        "queue_name": "",
                        "job_name": "",
                        "consumer_style": "process",
                        "callee_expr": callee_base + ".process",
                        "start_line": i,
                        "end_line": i,
                        "parse_level": "L2",
                    }
                )
    return out


def detect_ts_cache_ops(lines):
    out = []
    has_ioredis = "ioredis" in "\n".join(lines).lower()
    rx = re.compile(r"([A-Za-z0-9_$.]+)\.(get|mget|hget|set|hset|expire|del|unlink|hdel)\s*\(")
    for i, line in enumerate(lines, start=1):
        m = rx.search(line)
        if not m:
            continue
        callee_base = m.group(1)
        op = m.group(2).lower()
        lb = callee_base.lower()
        if not any(x in lb for x in ["redis", "cache", "client"]):
            continue
        event_kind = ""
        if op in ("get", "mget", "hget"):
            event_kind = "cache.read"
        elif op in ("set", "hset", "expire"):
            event_kind = "cache.write"
        elif op in ("del", "unlink", "hdel"):
            event_kind = "cache.invalidate"
        if not event_kind:
            continue
        key_literal = _extract_literal_arg(line)
        framework = "ioredis" if ("ioredis" in lb or has_ioredis) else "redis"
        out.append(
            {
                "framework": framework,
                "cache_op": op,
                "event_kind": event_kind,
                "key_literal": key_literal,
                "key_expr": key_literal or "",
                "callee_expr": callee_base + "." + op,
                "start_line": i,
                "end_line": i,
                "parse_level": "L2",
            }
        )
    return out
