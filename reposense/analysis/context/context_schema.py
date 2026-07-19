import hashlib


ROUTE_INTENTS = {
    "public_auth_entrypoint",
    "protected_auth_operation",
    "sensitive_business_operation",
    "unknown",
}
FILE_CONTEXTS = {
    "production",
    "generated",
    "seed",
    "template",
    "fixture",
    "test",
    "migration",
    "unknown",
}
REVIEW_MODIFIERS = {"normal", "downweight", "exclude_from_primary_review"}


def _stable_id(prefix, *parts):
    value = "|".join(str(part or "") for part in parts)
    return f"{prefix}-{hashlib.sha1(value.encode('utf-8')).hexdigest()[:12]}"


def normalize_route_intent(item):
    row = item if isinstance(item, dict) else {}
    method = str(row.get("method") or "").upper()
    path = str(row.get("path") or "")
    file_path = str(row.get("file") or "").replace("\\", "/")
    line = int(row.get("line_start") or 1)
    intent = str(row.get("intent") or "unknown")
    if intent not in ROUTE_INTENTS:
        intent = "unknown"
    signals = sorted({str(value) for value in (row.get("signals") or []) if str(value)})
    return {
        "annotation_id": str(
            row.get("annotation_id")
            or _stable_id("route-intent", method, path, file_path, line, intent, ",".join(signals))
        ),
        "method": method,
        "path": path,
        "file": file_path,
        "line_start": line,
        "intent": intent,
        "confidence": round(float(row.get("confidence") or 0.0), 4),
        "signals": signals,
        "evidence_refs": row.get("evidence_refs") if isinstance(row.get("evidence_refs"), list) else [],
        "limitations": sorted({str(value) for value in (row.get("limitations") or []) if str(value)}),
    }


def normalize_file_context(item):
    row = item if isinstance(item, dict) else {}
    file_path = str(row.get("file") or "").replace("\\", "/")
    context = str(row.get("context") or "unknown")
    if context not in FILE_CONTEXTS:
        context = "unknown"
    modifier = str(row.get("review_modifier") or "normal")
    if modifier not in REVIEW_MODIFIERS:
        modifier = "normal"
    signals = sorted({str(value) for value in (row.get("signals") or []) if str(value)})
    return {
        "annotation_id": str(
            row.get("annotation_id")
            or _stable_id("file-context", file_path, context, ",".join(signals))
        ),
        "file": file_path,
        "context": context,
        "confidence": round(float(row.get("confidence") or 0.0), 4),
        "signals": signals,
        "evidence_refs": row.get("evidence_refs") if isinstance(row.get("evidence_refs"), list) else [],
        "review_modifier": modifier,
        "limitations": sorted({str(value) for value in (row.get("limitations") or []) if str(value)}),
    }
