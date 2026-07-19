import hashlib
import json

from ...evidence.location import canonicalize_evidence_ref


ALLOWED_COVERAGE_STATUS = {
    "covered_explicit",
    "uncovered",
    "partially_covered",
    "read_only_transaction",
    "unknown",
}

ALLOWED_TRANSACTION_MECHANISMS = {
    "typeorm_callback",
    "entity_manager_callback",
    "query_runner",
    "trusted_decorator_method",
    "trusted_decorator_class",
    "direct_wrapper_caller",
    "none",
    "unknown",
}


def make_correlation_id(db_event_id, repository_type, operation, callsites):
    source = {
        "db_event_id": str(db_event_id or ""),
        "repository_type": str(repository_type or ""),
        "operation": str(operation or ""),
        "callsites": sorted(
            [
                (str(item.get("file") or ""), int(item.get("line") or 0), str(item.get("caller_method") or ""))
                for item in (callsites or [])
            ]
        ),
    }
    raw = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def _refs(values):
    out = []
    seen = set()
    for value in values if isinstance(values, list) else []:
        ref = canonicalize_evidence_ref(value)
        if ref is None:
            continue
        key = (ref["file"], ref["start_line"], ref["end_line"], str(ref.get("source_type") or ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(ref)
    return sorted(out, key=lambda x: (x["file"], x["start_line"], x["end_line"], str(x.get("source_type") or "")))


def normalize_correlation(raw):
    item = dict(raw or {})
    item["coverage_status"] = str(item.get("coverage_status") or "unknown")
    item["language"] = str(item.get("language") or "")
    item["framework"] = str(item.get("framework") or "")
    item["transaction_mechanism"] = str(
        item.get("transaction_mechanism") or "unknown"
    )
    item["confidence"] = round(float(item.get("confidence") or 0.0), 3)
    for key in [
        "caller_file",
        "caller_type",
        "caller_class",
        "caller_method",
        "target_file",
        "target_class",
        "target_method",
        "repository_receiver",
        "repository_type",
        "receiver_kind",
        "receiver_name",
        "operation",
        "db_operation_id",
    ]:
        item[key] = str(item.get(key) or "")
    line = item.get("callsite_line")
    item["callsite_line"] = int(line) if isinstance(line, int) and line >= 1 else None
    item["transaction_scope"] = str(item.get("transaction_scope") or "none")
    item["transaction_evidence_refs"] = _refs(item.get("transaction_evidence_refs"))
    item["callsite_evidence_refs"] = _refs(item.get("callsite_evidence_refs"))
    item["db_write_evidence_refs"] = _refs(item.get("db_write_evidence_refs"))
    item["limitations"] = sorted(set(str(x) for x in (item.get("limitations") or []) if str(x)))
    item["callsites"] = sorted(
        [dict(x) for x in (item.get("callsites") or []) if isinstance(x, dict)],
        key=lambda x: (str(x.get("file") or ""), int(x.get("line") or 0), str(x.get("caller_method") or "")),
    )
    if not item.get("correlation_id"):
        item["correlation_id"] = make_correlation_id(
            item.get("db_event_id"), item.get("repository_type"), item.get("operation"), item.get("callsites")
        )
    return item


def validate_correlation(raw):
    item = normalize_correlation(raw)
    errors = []
    if item["coverage_status"] not in ALLOWED_COVERAGE_STATUS:
        errors.append("coverage_status invalid")
    if item["transaction_mechanism"] not in ALLOWED_TRANSACTION_MECHANISMS:
        errors.append("transaction_mechanism invalid")
    if not item.get("correlation_id"):
        errors.append("correlation_id missing")
    if not item.get("db_event_id"):
        errors.append("db_event_id missing")
    if not item.get("db_write_evidence_refs"):
        errors.append("db_write_evidence_refs missing")
    if item["coverage_status"] != "unknown" and not item.get("callsite_evidence_refs"):
        errors.append("callsite_evidence_refs missing")
    if not 0.0 <= item["confidence"] <= 1.0:
        errors.append("confidence invalid")
    return errors


def stable_sort_correlations(values):
    return sorted(
        [normalize_correlation(value) for value in (values or [])],
        key=lambda x: (
            str(x.get("db_write_file") or ""),
            int(x.get("db_write_line") or 0),
            str(x.get("repository_type") or ""),
            str(x.get("operation") or ""),
            str(x.get("correlation_id") or ""),
        ),
    )
