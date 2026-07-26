import json
from collections import Counter, defaultdict
from pathlib import Path

from ...events.taxonomy import normalize_event_kind
from ...evidence.location import canonicalize_evidence_ref, filter_valid_evidence_refs
from .idempotency_extractor import (
    STRONG_GUARDS,
    analyze_consumer_idempotency,
)
from .reliability_schema import (
    normalize_correlation,
    stable_sort_correlations,
    stable_sort_risks,
)
from .retry_extractor import extract_retry_signals


def _read_json(path, default):
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return default


def _event_ref(run_root, repo_root, node):
    for evidence_id in node.get("evidence") or []:
        raw = _read_json(run_root / "evidence" / f"{evidence_id}.json", {})
        ref = canonicalize_evidence_ref(
            raw,
            repo_root=repo_root,
            allow_repo_absolute=True,
        )
        if ref is not None:
            ref["event_id"] = str(node.get("event_id") or "")
            return ref
    return None


def _channel_name(meta):
    name = str(meta.get("queue_name") or meta.get("topic_name") or "").strip()
    expression = str(meta.get("queue_name_expr") or "").strip()
    resolved = bool(meta.get("queue_name_resolved")) and bool(name)
    if resolved:
        if expression and expression.strip("\"'") != name:
            return name, "resolved_constant"
        return name, "resolved_static"
    if expression:
        return expression, "dynamic_expression"
    return "", "unknown"


def _channel_kind(framework):
    return "topic" if framework == "spring_kafka" else (
        "queue" if framework in {"bull", "bullmq", "spring_rabbit"} else "unknown"
    )


def _event_facts(run_dir, repo_root):
    run_root = Path(run_dir)
    graph = _read_json(run_root / "event_graph.json", {"nodes": []})
    facts = []
    for node in graph.get("nodes") or []:
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        kind = str(normalize_event_kind(node.get("type"), meta=meta) or "")
        ref = _event_ref(run_root, repo_root, node)
        if ref is None:
            continue
        framework = str(meta.get("framework") or "unknown").lower()
        fact = {
            "event_id": str(node.get("event_id") or ""),
            "kind": kind,
            "framework": framework,
            "meta": meta,
            "ref": ref,
            "confidence": float(node.get("confidence") or 0.0),
        }
        if kind in {"queue.dispatch", "queue.consume"}:
            name, resolution = _channel_name(meta)
            fact.update(
                {
                    "role": "producer" if kind == "queue.dispatch" else "consumer",
                    "queue_or_topic": name,
                    "name_resolution": resolution,
                    "channel_kind": _channel_kind(framework),
                }
            )
        facts.append(fact)
    return facts


def _dedupe_refs(refs):
    valid, _ = filter_valid_evidence_refs(refs)
    return valid


def _aggregate_retry(items):
    order = {
        "explicit_retry": 0,
        "explicit_no_retry": 1,
        "dynamic_or_unresolved": 2,
        "framework_default_or_unknown": 3,
    }
    candidates = [item for item in items if item]
    if not candidates:
        return "framework_default_or_unknown", {}, [], []
    chosen = sorted(
        candidates,
        key=lambda item: order.get(
            str(item.get("retry_status") or ""), 4
        ),
    )[0]
    refs = []
    limitations = []
    for item in candidates:
        refs.extend(item.get("evidence_refs") or [])
        limitations.extend(item.get("limitations") or [])
    return (
        str(chosen.get("retry_status") or "framework_default_or_unknown"),
        dict(chosen.get("retry_policy") or {}),
        _dedupe_refs(refs),
        sorted({str(value) for value in limitations if str(value)}),
    )


def _aggregate_identity(items):
    order = [
        "deduplication_option",
        "stable_job_id",
        "transport_idempotence_observed",
        "message_key_observed",
        "none_observed",
        "unknown",
    ]
    statuses = {
        str(item.get("producer_identity_status") or "")
        for item in items
        if item
    }
    for status in order:
        if status in statuses:
            return status
    return "unknown"


def _aggregate_consumers(consumers, analyses):
    side_effects = []
    handler_refs = []
    guard_refs = []
    limitations = []
    statuses = []
    for consumer in consumers:
        analysis = analyses.get(str(consumer.get("event_id") or ""), {})
        effects = analysis.get("consumer_side_effects") or []
        side_effects.extend(effects)
        handler_refs.extend(analysis.get("handler_refs") or [])
        guard_refs.extend(analysis.get("guard_evidence_refs") or [])
        limitations.extend(analysis.get("limitations") or [])
        if effects:
            statuses.append(
                str(
                    analysis.get("consumer_idempotency_status")
                    or "none_observed"
                )
            )
    if not statuses:
        status = "unknown"
    elif any(value == "none_observed" for value in statuses):
        status = "none_observed"
    elif any(value == "guard_signal_observed" for value in statuses):
        status = "guard_signal_observed"
    elif all(value in STRONG_GUARDS for value in statuses):
        priority = [
            "redis_atomic_guard_observed",
            "unique_constraint_observed",
            "inbox_or_processed_event_observed",
            "persistent_guard_observed",
        ]
        status = next(
            value for value in priority if value in set(statuses)
        )
    else:
        status = "unknown"
    unique_effects = {}
    for effect in side_effects:
        key = (
            effect.get("event_id"),
            effect.get("kind"),
            effect.get("file"),
            effect.get("line_start"),
        )
        unique_effects[key] = effect
    return {
        "status": status,
        "side_effects": list(unique_effects.values()),
        "handler_refs": _dedupe_refs(handler_refs),
        "guard_refs": _dedupe_refs(guard_refs),
        "limitations": sorted(
            {str(value) for value in limitations if str(value)}
        ),
    }


def _coverage(retry_status, identity_status, consumer_status, effects):
    strong_guard = consumer_status in STRONG_GUARDS
    if retry_status == "explicit_retry" and strong_guard:
        return "retry_with_consumer_guard"
    if retry_status == "explicit_retry" and effects:
        if identity_status not in {"none_observed", "unknown"}:
            return "retry_with_producer_dedupe_only"
        return "retry_without_consumer_guard"
    if (
        retry_status in {
            "framework_default_or_unknown",
            "dynamic_or_unresolved",
        }
        and effects
        and not strong_guard
    ):
        return "side_effect_without_guard"
    if retry_status == "explicit_no_retry":
        return "no_retry_observed"
    return "insufficient_evidence"


def _risk_for(correlation, retry_refs, consumer_data):
    if correlation["match_status"] != "matched":
        return None
    if correlation["name_resolution"] not in {
        "resolved_static",
        "resolved_constant",
    }:
        return None
    effects = correlation["consumer_side_effects"]
    if not effects:
        return None
    consumer_status = correlation["consumer_idempotency_status"]
    if consumer_status in STRONG_GUARDS:
        return None
    effect_refs = [
        ref
        for effect in effects
        for ref in (effect.get("evidence_refs") or [])
    ]
    if correlation["retry_status"] == "explicit_retry":
        pattern_type = "queue_retry_without_idempotency_guard"
        title = "Queue retry with side effects and no observed consumer idempotency guard"
        reason = (
            "Explicit retry and a consumer side effect were observed, but "
            "consumer-side persistent or atomic idempotency evidence was not observed."
        )
        refs = retry_refs + consumer_data["handler_refs"] + effect_refs
        limitations = [
            "consumer_idempotency_evidence_not_observed",
            "static_retry_configuration_may_differ_at_runtime",
        ]
    elif correlation["retry_status"] in {
        "framework_default_or_unknown",
        "dynamic_or_unresolved",
    }:
        pattern_type = "queue_consumer_side_effect_without_idempotency_evidence"
        title = "Queue consumer side effect without observed idempotency evidence"
        reason = (
            "A matched consumer side effect was observed while retry behavior "
            "is unknown or unresolved and no consumer idempotency guard was observed."
        )
        refs = consumer_data["handler_refs"] + effect_refs
        limitations = [
            "consumer_idempotency_evidence_not_observed",
            "retry_policy_unresolved",
        ]
    else:
        return None
    refs = _dedupe_refs(refs)
    if not refs:
        return None
    return {
        "pattern_type": pattern_type,
        "title": title,
        "severity": "medium",
        "status": "suspected",
        "confidence": min(float(correlation["confidence"]), 0.82),
        "correlation_id": correlation["correlation_id"],
        "framework": correlation["framework"],
        "queue_or_topic": correlation["queue_or_topic"],
        "reason": reason,
        "evidence_refs": refs,
        "limitations": sorted(
            set(limitations + list(correlation.get("limitations") or []))
        ),
        "suggested_human_review": True,
    }


def correlate_queue_reliability(run_dir, repo_root):
    facts = _event_facts(run_dir, repo_root)
    queue_facts = [
        fact
        for fact in facts
        if fact.get("kind") in {"queue.dispatch", "queue.consume"}
    ]
    retry_signals, global_config = extract_retry_signals(
        repo_root, queue_facts
    )
    consumers = [
        fact for fact in queue_facts if fact.get("role") == "consumer"
    ]
    consumer_analyses = analyze_consumer_idempotency(
        repo_root, consumers, facts
    )
    consumers_by_framework = Counter(
        str(item.get("framework") or "") for item in consumers
    )
    groups = defaultdict(list)
    for fact in queue_facts:
        if fact["name_resolution"] in {
            "resolved_static",
            "resolved_constant",
        }:
            key = (
                fact["framework"],
                fact["channel_kind"],
                fact["queue_or_topic"],
            )
        else:
            key = (
                fact["framework"],
                fact["channel_kind"],
                "__unknown__:" + fact["event_id"],
            )
        groups[key].append(fact)
    correlations = []
    risks = []
    for (framework, channel_kind, grouped_name), rows in sorted(groups.items()):
        producers = [row for row in rows if row["role"] == "producer"]
        grouped_consumers = [row for row in rows if row["role"] == "consumer"]
        resolution = rows[0]["name_resolution"]
        channel_name = (
            rows[0]["queue_or_topic"]
            if not grouped_name.startswith("__unknown__:")
            else ""
        )
        if resolution not in {"resolved_static", "resolved_constant"}:
            match_status = "unknown_name"
        elif producers and grouped_consumers:
            match_status = "matched"
        elif producers:
            match_status = "dispatch_only"
        else:
            match_status = "consume_only"
        signals = [
            retry_signals.get(str(row.get("event_id") or ""), {})
            for row in rows
        ]
        retry_status, retry_policy, retry_refs, retry_limits = (
            _aggregate_retry(signals)
        )
        if (
            retry_status == "framework_default_or_unknown"
            and len(global_config.get(framework) or []) == 1
            and consumers_by_framework.get(framework, 0) == 1
        ):
            retry_status = "explicit_retry"
            retry_policy = {"source": "application_error_handler"}
            retry_refs = _dedupe_refs(global_config[framework])
            retry_limits.append("application_scope_retry_configuration")
        identity = _aggregate_identity(signals)
        consumer_data = _aggregate_consumers(
            grouped_consumers, consumer_analyses
        )
        limitations = retry_limits + consumer_data["limitations"]
        if identity not in {"none_observed", "unknown"}:
            limitations.append(
                "producer_identity_does_not_prove_consumer_idempotency"
            )
        if match_status != "matched":
            limitations.append("producer_consumer_pair_not_confirmed")
        producer_refs = _dedupe_refs([row["ref"] for row in producers])
        consumer_refs = _dedupe_refs(
            [row["ref"] for row in grouped_consumers]
        )
        effect_refs = [
            ref
            for effect in consumer_data["side_effects"]
            for ref in effect.get("evidence_refs") or []
        ]
        evidence_refs = _dedupe_refs(
            producer_refs
            + consumer_refs
            + retry_refs
            + consumer_data["guard_refs"]
            + effect_refs
        )
        confidence_values = [
            float(row.get("confidence") or 0.0) for row in rows
        ]
        confidence = min(confidence_values) if confidence_values else 0.0
        if match_status != "matched":
            confidence = min(confidence, 0.62)
        correlation = normalize_correlation(
            {
                "framework": framework,
                "channel_kind": channel_kind,
                "queue_or_topic": channel_name,
                "name_resolution": resolution,
                "producer_refs": producer_refs,
                "consumer_refs": consumer_refs,
                "match_status": match_status,
                "retry_status": retry_status,
                "retry_policy": retry_policy,
                "producer_identity_status": identity,
                "consumer_idempotency_status": consumer_data["status"],
                "consumer_side_effects": consumer_data["side_effects"],
                "coverage_status": _coverage(
                    retry_status,
                    identity,
                    consumer_data["status"],
                    consumer_data["side_effects"],
                ),
                "confidence": confidence,
                "evidence_refs": evidence_refs,
                "limitations": limitations,
            }
        )
        correlations.append(correlation)
        risk = _risk_for(correlation, retry_refs, consumer_data)
        if risk:
            risks.append(risk)
    correlations = stable_sort_correlations(correlations)
    risks = stable_sort_risks(risks)
    return correlations, risks


def summarize_queue_reliability(correlations, risks):
    coverage = Counter(
        str(item.get("coverage_status") or "") for item in correlations
    )
    retry = Counter(str(item.get("retry_status") or "") for item in correlations)
    identity = Counter(
        str(item.get("producer_identity_status") or "")
        for item in correlations
    )
    guards = Counter(
        str(item.get("consumer_idempotency_status") or "")
        for item in correlations
    )
    return {
        "version": "queue_reliability_summary_v1",
        "total_correlations": len(correlations),
        "matched_channels": sum(
            1 for item in correlations if item.get("match_status") == "matched"
        ),
        "explicit_retries": int(retry.get("explicit_retry", 0)),
        "unresolved_retry_policies": int(
            retry.get("dynamic_or_unresolved", 0)
            + retry.get("framework_default_or_unknown", 0)
        ),
        "producer_dedupe_signals": int(
            identity.get("stable_job_id", 0)
            + identity.get("deduplication_option", 0)
            + identity.get("message_key_observed", 0)
        ),
        "transport_idempotence_signals": int(
            identity.get("transport_idempotence_observed", 0)
        ),
        "side_effecting_consumers": sum(
            1 for item in correlations if item.get("consumer_side_effects")
        ),
        "consumer_guards": sum(
            int(guards.get(status, 0)) for status in STRONG_GUARDS
        ),
        "retry_with_consumer_guard": int(
            coverage.get("retry_with_consumer_guard", 0)
        ),
        "retry_with_producer_dedupe_only": int(
            coverage.get("retry_with_producer_dedupe_only", 0)
        ),
        "retry_without_consumer_guard": int(
            coverage.get("retry_without_consumer_guard", 0)
        ),
        "side_effect_without_guard": int(
            coverage.get("side_effect_without_guard", 0)
        ),
        "actionable_suspected_risks": len(risks),
        "counts_by_coverage_status": dict(sorted(coverage.items())),
        "counts_by_framework": dict(
            sorted(
                Counter(
                    str(item.get("framework") or "unknown")
                    for item in correlations
                ).items()
            )
        ),
        "limitations": [
            "Correlation is limited to canonical queue facts and same-handler or uniquely resolved one-hop source evidence.",
            "Producer identity and transport idempotence do not prove consumer business idempotency.",
            "Missing guard evidence is not proof that no runtime guard exists.",
        ],
    }
