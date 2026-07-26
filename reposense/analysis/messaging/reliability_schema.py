import hashlib
import json

from ...evidence.location import filter_valid_evidence_refs


CHANNEL_KINDS = {"queue", "topic", "unknown"}
NAME_RESOLUTIONS = {
    "resolved_static",
    "resolved_constant",
    "dynamic_expression",
    "unknown",
}
MATCH_STATUSES = {
    "matched",
    "dispatch_only",
    "consume_only",
    "ambiguous",
    "unknown_name",
}
RETRY_STATUSES = {
    "explicit_retry",
    "explicit_no_retry",
    "framework_default_or_unknown",
    "dynamic_or_unresolved",
}
PRODUCER_IDENTITY_STATUSES = {
    "stable_job_id",
    "deduplication_option",
    "message_key_observed",
    "transport_idempotence_observed",
    "none_observed",
    "unknown",
}
CONSUMER_IDEMPOTENCY_STATUSES = {
    "persistent_guard_observed",
    "redis_atomic_guard_observed",
    "unique_constraint_observed",
    "inbox_or_processed_event_observed",
    "guard_signal_observed",
    "none_observed",
    "unknown",
}
COVERAGE_STATUSES = {
    "retry_with_consumer_guard",
    "retry_with_producer_dedupe_only",
    "retry_without_consumer_guard",
    "side_effect_without_guard",
    "no_retry_observed",
    "insufficient_evidence",
}


def _stable_id(prefix, payload):
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return prefix + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def stable_correlation_id(item):
    return _stable_id(
        "qrc-",
        {
            "framework": item.get("framework"),
            "channel_kind": item.get("channel_kind"),
            "queue_or_topic": item.get("queue_or_topic"),
            "match_status": item.get("match_status"),
            "producer_refs": [
                [ref.get("file"), ref.get("start_line"), ref.get("event_id")]
                for ref in item.get("producer_refs") or []
            ],
            "consumer_refs": [
                [ref.get("file"), ref.get("start_line"), ref.get("event_id")]
                for ref in item.get("consumer_refs") or []
            ],
        },
    )


def stable_risk_id(item):
    return _stable_id(
        "qrr-",
        {
            "pattern_type": item.get("pattern_type"),
            "correlation_id": item.get("correlation_id"),
            "evidence": [
                [ref.get("file"), ref.get("start_line"), ref.get("event_id")]
                for ref in item.get("evidence_refs") or []
            ],
        },
    )


def _enum(value, allowed, default):
    value = str(value or default)
    return value if value in allowed else default


def normalize_correlation(raw):
    item = dict(raw or {})
    item["framework"] = str(item.get("framework") or "unknown")
    item["channel_kind"] = _enum(
        item.get("channel_kind"), CHANNEL_KINDS, "unknown"
    )
    item["queue_or_topic"] = str(item.get("queue_or_topic") or "")
    item["name_resolution"] = _enum(
        item.get("name_resolution"), NAME_RESOLUTIONS, "unknown"
    )
    item["match_status"] = _enum(
        item.get("match_status"), MATCH_STATUSES, "unknown_name"
    )
    item["retry_status"] = _enum(
        item.get("retry_status"),
        RETRY_STATUSES,
        "framework_default_or_unknown",
    )
    item["producer_identity_status"] = _enum(
        item.get("producer_identity_status"),
        PRODUCER_IDENTITY_STATUSES,
        "unknown",
    )
    item["consumer_idempotency_status"] = _enum(
        item.get("consumer_idempotency_status"),
        CONSUMER_IDEMPOTENCY_STATUSES,
        "unknown",
    )
    item["coverage_status"] = _enum(
        item.get("coverage_status"),
        COVERAGE_STATUSES,
        "insufficient_evidence",
    )
    item["retry_policy"] = (
        item.get("retry_policy")
        if isinstance(item.get("retry_policy"), dict)
        else {}
    )
    for field in ("producer_refs", "consumer_refs", "evidence_refs"):
        refs, _ = filter_valid_evidence_refs(item.get(field))
        item[field] = refs
    item["consumer_side_effects"] = sorted(
        [
            effect
            for effect in (item.get("consumer_side_effects") or [])
            if isinstance(effect, dict)
        ],
        key=lambda effect: (
            str(effect.get("kind") or ""),
            str(effect.get("file") or ""),
            int(effect.get("line_start") or 0),
            str(effect.get("event_id") or ""),
        ),
    )
    item["confidence"] = round(float(item.get("confidence") or 0.0), 3)
    item["limitations"] = sorted(
        {str(value) for value in (item.get("limitations") or []) if str(value)}
    )
    item["correlation_id"] = str(
        item.get("correlation_id") or stable_correlation_id(item)
    )
    return item


def normalize_risk(raw):
    item = dict(raw or {})
    item["pattern_type"] = str(item.get("pattern_type") or "")
    item["severity"] = str(item.get("severity") or "medium").lower()
    item["status"] = "suspected"
    item["confidence"] = round(float(item.get("confidence") or 0.0), 3)
    refs, invalid = filter_valid_evidence_refs(item.get("evidence_refs"))
    item["evidence_refs"] = refs
    limitations = list(item.get("limitations") or [])
    if invalid:
        limitations.append("invalid_evidence_ref_omitted")
    item["limitations"] = sorted(
        {str(value) for value in limitations if str(value)}
    )
    item["risk_id"] = str(item.get("risk_id") or stable_risk_id(item))
    return item


def stable_sort_correlations(items):
    return sorted(
        [normalize_correlation(item) for item in items],
        key=lambda item: (
            item["framework"],
            item["channel_kind"],
            item["queue_or_topic"],
            item["correlation_id"],
        ),
    )


def stable_sort_risks(items):
    return sorted(
        [normalize_risk(item) for item in items],
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}.get(item["severity"], 1),
            item["pattern_type"],
            item["risk_id"],
        ),
    )
