import re


_HTTP_VERBS = {"GET", "POST", "PUT", "DELETE", "PATCH"}
_SKIP_METHOD_NAMES = {"if", "for", "while", "switch", "catch", "return", "new"}


def _norm_path(a, b=""):
    x = str(a or "").strip()
    y = str(b or "").strip()
    if x and not x.startswith("/"):
        x = "/" + x
    if y and not y.startswith("/"):
        y = "/" + y
    s = (x.rstrip("/") + "/" + y.lstrip("/")) if y else x
    s = re.sub(r"/+", "/", s)
    if not s:
        s = "/"
    if s != "/" and s.endswith("/"):
        s = s[:-1]
    return s


def _extract_first_quoted(s):
    m = re.search(r'["\']([^"\']+)["\']', s or "")
    return m.group(1) if m else ""


def _extract_path_literal(args):
    a = str(args or "").strip()
    if not a:
        return ""
    if "+" in a:
        return None
    m = re.search(r"(?:path|value)\s*=\s*\{([^}]+)\}", a)
    if m:
        return _extract_first_quoted(m.group(1))
    m = re.search(r"(?:path|value)\s*=\s*([\"'][^\"']+[\"'])", a)
    if m:
        return _extract_first_quoted(m.group(1))
    m = re.search(r"\{([^}]+)\}", a)
    if m:
        v = _extract_first_quoted(m.group(1))
        if v:
            return v
    return _extract_first_quoted(a)


def _extract_method_from_request_mapping(args):
    a = str(args or "")
    m = re.search(r"RequestMethod\.(GET|POST|PUT|DELETE|PATCH)", a, flags=re.I)
    if m:
        return m.group(1).upper()
    return ""


def _parse_annotation(ann):
    t = str(ann or "").strip()
    m = re.match(r"@([A-Za-z0-9_$.]+)\s*(?:\((.*)\))?$", t)
    if not m:
        return "", ""
    name = m.group(1).split(".")[-1]
    args = m.group(2) or ""
    return name, args


def _parse_imports(lines):
    src = "unknown"
    for line in lines:
        m = re.search(r"^\s*import\s+([A-Za-z0-9_.]+)\s*;", line)
        if not m:
            continue
        imp = m.group(1)
        if imp.endswith(".Transactional"):
            if imp.startswith("org.springframework."):
                return "org.springframework.transaction.annotation.Transactional"
            if imp.startswith("jakarta.transaction."):
                src = "jakarta.transaction.Transactional"
            elif imp.startswith("javax.transaction."):
                src = "javax.transaction.Transactional"
    return src


def _collect_annotations(lines, start_idx):
    anns = []
    i = start_idx
    while i < len(lines):
        t = lines[i].strip()
        if not t.startswith("@"):
            break
        ann = t
        bal = ann.count("(") - ann.count(")")
        while bal > 0 and (i + 1) < len(lines):
            i += 1
            nxt = lines[i].strip()
            ann += " " + nxt
            bal += nxt.count("(") - nxt.count(")")
        anns.append({"text": ann, "line": i + 1})
        i += 1
    return anns, i


def detect_java_spring_routes(lines):
    routes = []
    class_stack = []
    pending = []
    i = 0
    brace = 0
    while i < len(lines):
        t = lines[i].strip()
        if t.startswith("@"):
            pending, i = _collect_annotations(lines, i)
            continue
        cm = re.search(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\b", t)
        if cm:
            cname = cm.group(1)
            is_controller = False
            class_prefix = ""
            for a in pending:
                n, args = _parse_annotation(a["text"])
                if n in ("RestController", "Controller"):
                    is_controller = True
                if n == "RequestMapping":
                    p = _extract_path_literal(args)
                    if p is None:
                        class_prefix = ""
                    elif p:
                        class_prefix = p
            class_stack.append({
                "name": cname,
                "is_controller": is_controller,
                "prefix": class_prefix,
                "depth_start": brace + t.count("{") - t.count("}"),
            })
            pending = []
        mm = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*(?:\{|throws\b)", t)
        if mm and pending:
            mname = mm.group(1)
            if mname not in _SKIP_METHOD_NAMES:
                cur = class_stack[-1] if class_stack else {"name": "", "is_controller": False, "prefix": ""}
                for a in pending:
                    n, args = _parse_annotation(a["text"])
                    verb = ""
                    path = ""
                    if n in ("GetMapping", "PostMapping", "PutMapping", "DeleteMapping", "PatchMapping"):
                        verb = n.replace("Mapping", "").upper()
                        path = _extract_path_literal(args)
                    elif n == "RequestMapping":
                        verb = _extract_method_from_request_mapping(args) or "GET"
                        path = _extract_path_literal(args)
                    if verb not in _HTTP_VERBS:
                        continue
                    if path is None:
                        continue
                    base = cur.get("prefix") or ""
                    full = _norm_path(base, path or "")
                    if not full:
                        continue
                    routes.append({
                        "method": verb,
                        "path": full,
                        "start_line": int(a["line"]),
                        "end_line": int(a["line"]),
                        "controller_class": cur.get("name") or "",
                        "handler_method": mname,
                        "annotation_kind": n,
                        "framework": "spring",
                        "parse_level": "L2",
                    })
            pending = []
        brace += t.count("{") - t.count("}")
        while class_stack and brace < class_stack[-1]["depth_start"]:
            class_stack.pop()
        i += 1
    routes.sort(key=lambda x: (x["controller_class"], x["handler_method"], x["start_line"], x["method"], x["path"]))
    return routes


def detect_java_transactions(lines):
    out = []
    ann_src = _parse_imports(lines)
    class_stack = []
    pending = []
    i = 0
    brace = 0
    while i < len(lines):
        t = lines[i].strip()
        if t.startswith("@"):
            pending, i = _collect_annotations(lines, i)
            continue
        cm = re.search(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\b", t)
        if cm:
            cname = cm.group(1)
            tx_line = 0
            for a in pending:
                n, _ = _parse_annotation(a["text"])
                if n == "Transactional":
                    tx_line = int(a["line"])
                    out.append({
                        "scope": "class",
                        "class_name": cname,
                        "method_name": "",
                        "start_line": int(a["line"]),
                        "end_line": int(a["line"]),
                        "annotation_source": ann_src,
                        "transaction_style": "@Transactional",
                        "framework": "spring",
                        "parse_level": "L2",
                    })
            class_stack.append({"name": cname, "depth_start": brace + t.count("{") - t.count("}"), "tx_line": tx_line})
            pending = []
        mm = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*(?:\{|throws\b)", t)
        if mm and pending:
            mname = mm.group(1)
            if mname not in _SKIP_METHOD_NAMES:
                cur = class_stack[-1] if class_stack else {"name": ""}
                for a in pending:
                    n, _ = _parse_annotation(a["text"])
                    if n == "Transactional":
                        out.append({
                            "scope": "method",
                            "class_name": cur.get("name") or "",
                            "method_name": mname,
                            "start_line": int(a["line"]),
                            "end_line": int(a["line"]),
                            "annotation_source": ann_src,
                            "transaction_style": "@Transactional",
                            "framework": "spring",
                            "parse_level": "L2",
                        })
            pending = []
        brace += t.count("{") - t.count("}")
        while class_stack and brace < class_stack[-1]["depth_start"]:
            class_stack.pop()
        i += 1
    out.sort(key=lambda x: (x["class_name"], x["scope"], x["method_name"], x["start_line"]))
    return out


def _collect_java_template_aliases(lines):
    kafka_alias = set()
    rabbit_alias = set()
    repo_alias = set()
    mapper_alias = set()
    em_alias = set()
    sqls_alias = set()
    for line in lines:
        t = line.strip()
        mk = re.search(r"\b([A-Za-z0-9_$.<>]+KafkaTemplate)\s+([A-Za-z_][A-Za-z0-9_]*)\b", t)
        if mk:
            kafka_alias.add(mk.group(2))
        mr = re.search(r"\b([A-Za-z0-9_$.<>]+RabbitTemplate)\s+([A-Za-z_][A-Za-z0-9_]*)\b", t)
        if mr:
            rabbit_alias.add(mr.group(2))
        mrepo = re.search(r"\b([A-Za-z0-9_$.<>]*Repository)\s+([A-Za-z_][A-Za-z0-9_]*)\b", t)
        if mrepo:
            repo_alias.add(mrepo.group(2))
        mmap = re.search(r"\b([A-Za-z0-9_$.<>]*Mapper)\s+([A-Za-z_][A-Za-z0-9_]*)\b", t)
        if mmap:
            mapper_alias.add(mmap.group(2))
        mem = re.search(r"\b(?:EntityManager)\s+([A-Za-z_][A-Za-z0-9_]*)\b", t)
        if mem:
            em_alias.add(mem.group(1))
        mss = re.search(r"\b(?:SqlSession)\s+([A-Za-z_][A-Za-z0-9_]*)\b", t)
        if mss:
            sqls_alias.add(mss.group(1))
    if "kafkaTemplate" not in kafka_alias:
        for line in lines:
            if "KafkaTemplate" in line:
                kafka_alias.add("kafkaTemplate")
                break
    if "rabbitTemplate" not in rabbit_alias:
        for line in lines:
            if "RabbitTemplate" in line:
                rabbit_alias.add("rabbitTemplate")
                break
    if "entityManager" not in em_alias:
        for line in lines:
            if "EntityManager" in line:
                em_alias.add("entityManager")
                break
    if "sqlSession" not in sqls_alias:
        for line in lines:
            if "SqlSession" in line:
                sqls_alias.add("sqlSession")
                break
    return kafka_alias, rabbit_alias, repo_alias, mapper_alias, em_alias, sqls_alias


def _java_string_constants(lines):
    constants = {}
    pattern = re.compile(
        r"\b(?:public|private|protected)?\s*"
        r"(?:static\s+)?(?:final\s+)?String\s+"
        r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([\"'])(.*?)\2"
    )
    for line in lines:
        match = pattern.search(line)
        if match:
            constants[match.group(1)] = match.group(3)
    return constants


def _split_java_arguments(text):
    value = str(text or "").strip()
    if value.startswith("("):
        value = value[1:]
    if value.endswith(")"):
        value = value[:-1]
    out = []
    current = []
    quote = ""
    escaped = False
    depth = 0
    for char in value:
        if quote:
            current.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
        elif char in "({[":
            depth += 1
            current.append(char)
        elif char == ")" and depth == 0:
            break
        elif char in ")}]":
            depth = max(0, depth - 1)
            current.append(char)
        elif char == "," and depth == 0:
            out.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        out.append("".join(current).strip())
    return out


def _resolve_java_destination(expression, constants):
    expr = str(expression or "").strip()
    literal = re.fullmatch(r"([\"'])(.*?)\1", expr, re.S)
    if literal:
        return literal.group(2), expr, True
    symbol = expr.split(".")[-1]
    if symbol in constants:
        return constants[symbol], expr, True
    return "", expr[:300], False


def _annotation_destination(args, keys, constants):
    value = str(args or "").strip()
    expression = ""
    for key in keys:
        match = re.search(
            rf"\b{re.escape(key)}\s*=\s*(\{{[^}}]*\}}|[^,]+)",
            value,
        )
        if match:
            expression = match.group(1).strip()
            break
    if not expression:
        expression = (_split_java_arguments(value) or [""])[0]
    if expression.startswith("{") and expression.endswith("}"):
        expression = (_split_java_arguments(expression[1:-1]) or [""])[0]
    return _resolve_java_destination(expression, constants)


def detect_java_queue_events(lines):
    out = []
    unsupported = []
    class_stack = []
    pending = []
    i = 0
    brace = 0
    kafka_alias, rabbit_alias, _, _, _, _ = _collect_java_template_aliases(lines)
    constants = _java_string_constants(lines)
    while i < len(lines):
        t = lines[i].strip()
        if t.startswith("@"):
            pending, i = _collect_annotations(lines, i)
            continue
        cm = re.search(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\b", t)
        if cm:
            class_stack.append({"name": cm.group(1), "depth_start": brace + t.count("{") - t.count("}")})
            pending = []
        mm = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*(?:\{|throws\b)", t)
        if mm and pending:
            mname = mm.group(1)
            if mname not in _SKIP_METHOD_NAMES:
                cur = class_stack[-1] if class_stack else {"name": ""}
                for a in pending:
                    n, args = _parse_annotation(a["text"])
                    if n == "KafkaListener":
                        tp, tp_expr, tp_resolved = _annotation_destination(
                            args,
                            ("topics", "topicPattern"),
                            constants,
                        )
                        if tp or tp_expr:
                            out.append({
                                "event_kind": "queue.consume",
                                "queue_system": "kafka",
                                "topic_name": tp,
                                "queue_name_expr": tp_expr,
                                "queue_name_resolved": tp_resolved,
                                "framework": "spring_kafka",
                                "listener_style": "@KafkaListener",
                                "class_name": cur.get("name") or "",
                                "method_name": mname,
                                "start_line": int(a["line"]),
                                "end_line": int(a["line"]),
                                "confidence": 0.84,
                            })
                    if n == "RabbitListener":
                        qn, qn_expr, qn_resolved = _annotation_destination(
                            args,
                            ("queues", "queuesToDeclare"),
                            constants,
                        )
                        if qn or qn_expr:
                            out.append({
                                "event_kind": "queue.consume",
                                "queue_system": "rabbitmq",
                                "queue_name": qn,
                                "queue_name_expr": qn_expr,
                                "queue_name_resolved": qn_resolved,
                                "framework": "spring_rabbit",
                                "listener_style": "@RabbitListener",
                                "class_name": cur.get("name") or "",
                                "method_name": mname,
                                "start_line": int(a["line"]),
                                "end_line": int(a["line"]),
                                "confidence": 0.84,
                            })
            pending = []
        for ka in sorted(kafka_alias):
            mk = re.search(rf"\b{re.escape(ka)}\.send\s*\(", t)
            if mk:
                arguments = _split_java_arguments(t[mk.end() - 1 :])
                topic, topic_expr, topic_resolved = _resolve_java_destination(
                    arguments[0] if arguments else "",
                    constants,
                )
                if not topic and not topic_expr:
                    continue
                out.append({
                    "event_kind": "queue.dispatch",
                    "queue_system": "kafka",
                    "topic_name": topic,
                    "queue_name_expr": topic_expr,
                    "queue_name_resolved": topic_resolved,
                    "framework": "spring_kafka",
                    "dispatch_style": "KafkaTemplate.send",
                    "callee_expr": f"{ka}.send",
                    "class_name": (class_stack[-1]["name"] if class_stack else ""),
                    "method_name": "",
                    "start_line": i + 1,
                    "end_line": i + 1,
                    "confidence": 0.82,
                })
        for ra in sorted(rabbit_alias):
            mr = re.search(rf"\b{re.escape(ra)}\.convertAndSend\s*\(", t)
            if mr:
                arguments = _split_java_arguments(t[mr.end() - 1 :])
                item = {
                    "event_kind": "queue.dispatch",
                    "queue_system": "rabbitmq",
                    "framework": "spring_rabbit",
                    "dispatch_style": "RabbitTemplate.convertAndSend",
                    "callee_expr": f"{ra}.convertAndSend",
                    "class_name": (class_stack[-1]["name"] if class_stack else ""),
                    "method_name": "",
                    "start_line": i + 1,
                    "end_line": i + 1,
                    "confidence": 0.82,
                }
                if len(arguments) >= 3:
                    exchange, exchange_expr, exchange_resolved = (
                        _resolve_java_destination(arguments[0], constants)
                    )
                    routing, routing_expr, routing_resolved = (
                        _resolve_java_destination(arguments[1], constants)
                    )
                    item["exchange"] = exchange
                    item["exchange_expr"] = exchange_expr
                    item["routing_key"] = routing
                    item["routing_key_expr"] = routing_expr
                    item["queue_name"] = ""
                    item["queue_name_expr"] = routing_expr
                    item["queue_name_resolved"] = False
                    item["destination_resolved"] = bool(
                        exchange_resolved and routing_resolved
                    )
                elif len(arguments) >= 2:
                    queue, queue_expr, queue_resolved = (
                        _resolve_java_destination(arguments[0], constants)
                    )
                    item["queue_name"] = queue
                    item["queue_name_expr"] = queue_expr
                    item["queue_name_resolved"] = queue_resolved
                else:
                    continue
                out.append(item)
        brace += t.count("{") - t.count("}")
        while class_stack and brace < class_stack[-1]["depth_start"]:
            class_stack.pop()
        i += 1
    text = "\n".join(lines)
    if "KafkaTemplate" in text and not any(x.get("queue_system") == "kafka" and x.get("event_kind") == "queue.dispatch" for x in out):
        unsupported.append({"type": "unsupported_detected", "language": "java", "framework": "spring_kafka", "path": "", "line_start": 0, "reason": "saw_KafkaTemplate_import_but_no_explicit_send"})
    if ("Repository" in text or "JpaRepository" in text) and "save(" not in text and "findById(" not in text and "findAll(" not in text and "existsById(" not in text:
        unsupported.append({"type": "unsupported_detected", "language": "java", "framework": "jpa", "path": "", "line_start": 0, "reason": "saw_Repository_field_but_no_explicit_supported_op"})
    if "Mapper" in text and "insert(" not in text and "update(" not in text and "delete(" not in text and "select" not in text:
        unsupported.append({"type": "unsupported_detected", "language": "java", "framework": "mybatis", "path": "", "line_start": 0, "reason": "saw_Mapper_but_method_name_non_standard_skipped"})
    out.sort(key=lambda x: (x.get("event_kind") or "", x.get("queue_system") or "", x.get("start_line") or 0))
    return {"events": out, "unsupported": unsupported}


def detect_java_db_ops(lines):
    out = []
    _, _, repo_alias, mapper_alias, em_alias, sqls_alias = _collect_java_template_aliases(lines)
    class_stack = []
    pending = []
    i = 0
    brace = 0
    method_names = ["save", "saveAll", "deleteById", "delete", "findById", "findAll", "existsById"]
    while i < len(lines):
        t = lines[i].strip()
        if t.startswith("@"):
            pending, i = _collect_annotations(lines, i)
            continue
        cm = re.search(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\b", t)
        if cm:
            class_stack.append({"name": cm.group(1), "depth_start": brace + t.count("{") - t.count("}")})
            pending = []
        cur_class = class_stack[-1]["name"] if class_stack else ""
        for ra in sorted(repo_alias):
            for mn in method_names:
                m = re.search(rf"\b{re.escape(ra)}\.{mn}\s*\(", t)
                if m:
                    op = "write"
                    if mn.startswith("find"):
                        op = "read"
                    elif mn.startswith("exists"):
                        op = "exists"
                    elif mn.startswith("delete"):
                        op = "delete"
                    out.append({
                        "event_kind": "db.read" if op in ("read", "exists") else "db.write",
                        "db_style": "jpa_repository",
                        "db_op": op,
                        "repo_symbol": ra,
                        "entity_hint": "",
                        "class_name": cur_class,
                        "method_name": "",
                        "start_line": i + 1,
                        "end_line": i + 1,
                        "confidence": 0.82,
                    })
        for em in sorted(em_alias):
            for mn, op in [("persist", "write"), ("merge", "write"), ("remove", "delete"), ("find", "read")]:
                m = re.search(rf"\b{re.escape(em)}\.{mn}\s*\(", t)
                if m:
                    out.append({
                        "event_kind": "db.read" if op == "read" else "db.write",
                        "db_style": "entity_manager",
                        "db_op": op,
                        "callee_expr": f"{em}.{mn}",
                        "class_name": cur_class,
                        "method_name": "",
                        "start_line": i + 1,
                        "end_line": i + 1,
                        "confidence": 0.84,
                    })
        for ma in sorted(mapper_alias):
            for mn, op in [("insert", "write"), ("update", "write"), ("delete", "delete"), ("selectOne", "read"), ("selectList", "read"), ("select", "read")]:
                m = re.search(rf"\b{re.escape(ma)}\.{mn}[A-Za-z0-9_]*\s*\(", t)
                if m:
                    out.append({
                        "event_kind": "db.read" if op == "read" else "db.write",
                        "db_style": "mybatis_mapper",
                        "db_op": op,
                        "mapper_symbol": ma,
                        "statement_hint": mn,
                        "class_name": cur_class,
                        "method_name": "",
                        "start_line": i + 1,
                        "end_line": i + 1,
                        "confidence": 0.8,
                    })
        for sa in sorted(sqls_alias):
            for mn, op in [("insert", "write"), ("update", "write"), ("delete", "delete"), ("selectOne", "read"), ("selectList", "read")]:
                m = re.search(rf"\b{re.escape(sa)}\.{mn}\s*\(", t)
                if m:
                    out.append({
                        "event_kind": "db.read" if op == "read" else "db.write",
                        "db_style": "sql_session",
                        "db_op": op,
                        "mapper_symbol": sa,
                        "statement_hint": mn,
                        "class_name": cur_class,
                        "method_name": "",
                        "start_line": i + 1,
                        "end_line": i + 1,
                        "confidence": 0.82,
                    })
        brace += t.count("{") - t.count("}")
        while class_stack and brace < class_stack[-1]["depth_start"]:
            class_stack.pop()
        i += 1
    out.sort(key=lambda x: (x.get("event_kind") or "", x.get("db_style") or "", x.get("start_line") or 0))
    return out
