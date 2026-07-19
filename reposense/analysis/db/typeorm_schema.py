import hashlib


KINDS = {"db.read", "db.write", "db.transaction", "db.query_unknown"}
RECEIVER_KINDS = {
    "repository",
    "entity_manager",
    "data_source",
    "query_runner",
    "query_builder",
    "base_entity",
    "unknown",
}


def stable_operation_id(item):
    raw = "|".join(
        str(item.get(key) or "")
        for key in ("kind", "operation", "receiver_kind", "receiver_name", "file", "line_start")
    )
    return "typeorm-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def normalize_operation(item):
    out = dict(item or {})
    out["kind"] = str(out.get("kind") or "db.query_unknown")
    if out["kind"] not in KINDS:
        raise ValueError(f"unsupported TypeORM operation kind: {out['kind']}")
    out["receiver_kind"] = str(out.get("receiver_kind") or "unknown")
    if out["receiver_kind"] not in RECEIVER_KINDS:
        raise ValueError(f"unsupported TypeORM receiver kind: {out['receiver_kind']}")
    out["line_start"] = int(out.get("line_start") or 0)
    out["line_end"] = int(out.get("line_end") or out["line_start"])
    if out["line_start"] < 1 or out["line_end"] < out["line_start"]:
        raise ValueError("TypeORM operation requires a valid positive line range")
    out["operation_id"] = str(out.get("operation_id") or stable_operation_id(out))
    out["file"] = str(out.get("file") or "").replace("\\", "/")
    out["operation"] = str(out.get("operation") or "")
    out["receiver_name"] = str(out.get("receiver_name") or "")
    out["entity"] = str(out.get("entity") or "")
    out["scope"] = out.get("scope") if isinstance(out.get("scope"), dict) else {}
    out["transaction_context"] = str(out.get("transaction_context") or "unknown")
    out["confidence"] = float(out.get("confidence") or 0.0)
    out["evidence_refs"] = [
        ref for ref in (out.get("evidence_refs") or []) if isinstance(ref, dict)
    ]
    out["signals"] = sorted(set(str(value) for value in (out.get("signals") or []) if value))
    out["limitations"] = sorted(set(str(value) for value in (out.get("limitations") or []) if value))
    return out
