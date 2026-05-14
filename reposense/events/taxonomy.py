EVENT_KINDS = [
    "api.route",
    "db.transaction",
    "db.read",
    "db.write",
    "queue.dispatch",
    "queue.consume",
    "cache.read",
    "cache.write",
    "cache.invalidate",
    "job.schedule",
    "job.execute",
]

EVENT_FAMILY = {
    "api.route": "api",
    "db.transaction": "db",
    "db.read": "db",
    "db.write": "db",
    "queue.dispatch": "queue",
    "queue.consume": "queue",
    "cache.read": "cache",
    "cache.write": "cache",
    "cache.invalidate": "cache",
    "job.schedule": "job",
    "job.execute": "job",
}

SUPPORTED_LANGUAGES = {"python", "sql", "openapi", "typescript", "java", "go", "unknown"}

SUPPORTED_FRAMEWORKS = {
    "fastapi",
    "flask",
    "django",
    "celery",
    "express",
    "nestjs",
    "prisma",
    "typeorm",
    "bull",
    "bullmq",
    "openapi",
    "sql",
    "redis",
    "ioredis",
    "spring",
    "spring_mvc",
    "spring_boot",
    "spring_kafka",
    "spring_rabbit",
    "jpa",
    "mybatis",
    "unknown",
}


def is_valid_event_kind(kind):
    return kind in EVENT_FAMILY


def event_family(kind):
    return EVENT_FAMILY.get(kind, "unknown")


def normalize_language(value):
    s = str(value or "").strip().lower()
    if s in SUPPORTED_LANGUAGES:
        return s
    if s in ("py",):
        return "python"
    return "unknown"


def normalize_framework(value):
    s = str(value or "").strip().lower()
    if s in SUPPORTED_FRAMEWORKS:
        return s
    if s.startswith("django"):
        return "django"
    if s.startswith("spring"):
        return "spring"
    return "unknown"


def normalize_event_kind(event_type, meta=None):
    t = str(event_type or "").strip().lower()
    m = meta or {}
    if t == "api":
        return "api.route"
    if t == "tx_boundary":
        return "db.transaction"
    if t == "db_op":
        dk = str(m.get("db.kind") or "").lower()
        if dk in ("db.read", "db.write"):
            return dk
        op = str(m.get("db.op") or "").lower()
        if op in ("read", "exists", "find", "select"):
            return "db.read"
        return "db.write"
    if t == "queue_dispatch":
        return "queue.dispatch"
    if t == "queue_consume":
        return "queue.consume"
    if t == "cache_op":
        ck = str(m.get("cache.kind") or "").lower()
        if ck in ("cache.read", "cache.write", "cache.invalidate"):
            return ck
        op = str(m.get("cache.op") or "").lower()
        if op in ("get", "read", "mget"):
            return "cache.read"
        if op in ("delete", "del", "invalidate", "evict", "unlink", "hdel"):
            return "cache.invalidate"
        return "cache.write"
    return None
