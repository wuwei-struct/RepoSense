from .taxonomy import normalize_event_kind, event_family, normalize_framework, normalize_language


def infer_language_framework_from_finding(finding, meta=None):
    f = finding or {}
    m = meta or {}
    pk = str(m.get("python.kind") or "")
    matcher = str(m.get("ast.matcher") or "")
    evs = str(m.get("evidence_strength") or "")
    if pk or matcher.startswith("py_"):
        fw = "unknown"
        if "fastapi" in matcher:
            fw = "fastapi"
        elif "flask" in matcher:
            fw = "flask"
        elif "django" in matcher:
            fw = "django"
        elif "celery" in matcher or "celery" in pk:
            fw = "celery"
        elif "cache" in matcher:
            fw = "redis" if "redis" in pk else "django"
        return "python", normalize_framework(fw)
    if evs == "openapi" or "http.method" in m:
        return "openapi", "openapi"
    tsk = str(m.get("ts.kind") or "").lower()
    if str(m.get("language") or "").lower() == "typescript" or tsk.startswith("route_") or tsk.startswith("transaction_") or tsk.startswith("queue_") or tsk == "cache_op":
        fw = str(m.get("framework") or "").lower()
        if not fw:
            if "express" in tsk:
                fw = "express"
            elif "nest" in tsk:
                fw = "nestjs"
            elif "prisma" in tsk:
                fw = "prisma"
            elif "typeorm" in tsk:
                fw = "typeorm"
            elif "queue" in tsk:
                fw = "bullmq"
            elif "cache" in tsk:
                fw = "redis"
        return "typescript", normalize_framework(fw)
    if str(m.get("language") or "").lower() == "java" or str(m.get("java.kind") or "").startswith(("route_", "queue_", "db_")) or str(m.get("tx.kind") or "") == "java_transactional":
        return "java", normalize_framework(str(m.get("framework") or "spring"))
    if m.get("tx.kind") == "sql_begin_commit":
        return "sql", "sql"
    return "unknown", "unknown"


def graph_node_to_unified_event(node):
    n = node or {}
    meta = n.get("meta") or {}
    kind = normalize_event_kind(n.get("type"), meta=meta)
    if not kind:
        return None
    lang = normalize_language(meta.get("language"))
    if lang == "unknown":
        txk = str(meta.get("tx.kind") or "")
        if kind == "db.transaction" and txk.startswith("sql"):
            lang = "sql"
        elif txk == "java_transactional" or str(meta.get("language") or "").lower() == "java":
            lang = "java"
        elif str(meta.get("language") or "").lower() == "typescript" or txk.startswith("ts_") or str(meta.get("framework") or "").lower() in ("express", "nestjs", "prisma", "typeorm", "bull", "bullmq", "redis", "ioredis"):
            lang = "typescript"
        elif kind == "api.route" and str(meta.get("source") or "") == "openapi":
            lang = "openapi"
        else:
            lang = "python"
    fw = normalize_framework(meta.get("framework"))
    if fw == "unknown":
        if kind == "api.route":
            if lang == "openapi":
                fw = "openapi"
            elif lang == "typescript":
                fw = "express"
            elif lang == "java":
                fw = "spring"
            else:
                fw = "fastapi"
        elif kind.startswith("queue."):
            qk = str(meta.get("queue.kind") or "").lower()
            if "bull" in qk:
                fw = "bullmq" if "mq" in qk else "bull"
            elif lang == "java":
                qs = str(meta.get("queue.system") or "").lower()
                fw = "spring_rabbit" if qs == "rabbitmq" else "spring_kafka"
            elif lang == "typescript":
                fw = "bullmq"
            else:
                fw = "celery"
        elif kind.startswith("db."):
            txk = str(meta.get("tx.kind") or "")
            if lang == "sql":
                fw = "sql"
            elif lang == "typescript" and "prisma" in txk:
                fw = "prisma"
            elif lang == "typescript" and "typeorm" in txk:
                fw = "typeorm"
            elif lang == "java":
                ds = str(meta.get("db_style") or "").lower()
                if "mybatis" in ds or "sql_session" in ds:
                    fw = "mybatis"
                elif "jpa" in ds or "entity_manager" in ds:
                    fw = "jpa"
                else:
                    fw = "spring"
            else:
                fw = "django"
        elif kind.startswith("cache."):
            cb = str(meta.get("cache.backend") or "").lower()
            if cb in ("redis", "ioredis"):
                fw = cb
            elif lang == "typescript":
                fw = "redis"
            else:
                fw = "django"
    return {
        "event_kind": kind,
        "event_family": event_family(kind),
        "language": lang,
        "framework": fw,
        "source_detector": str(meta.get("source") or "unknown"),
        "parse_level": str(meta.get("parse_level") or "L3"),
        "confidence": float(n.get("confidence") or 0.0),
        "evidence_ids": list(n.get("evidence") or []),
        "location": {"path": meta.get("path"), "start_line": meta.get("start_line"), "end_line": meta.get("end_line")},
        "meta": meta,
        "event_id": n.get("event_id"),
        "raw_type": n.get("type"),
    }


def collect_detected_languages_frameworks(findings, graph_nodes):
    langs = set()
    fws = set()
    for f in findings or []:
        meta = (f.get("meta") or {})
        lg, fw = infer_language_framework_from_finding(f, meta)
        langs.add(normalize_language(lg))
        fws.add(normalize_framework(fw))
    for n in graph_nodes or []:
        u = graph_node_to_unified_event(n)
        if not u:
            continue
        langs.add(u["language"])
        fws.add(u["framework"])
    return sorted(list(langs)), sorted(list(fws))
