"""Read-only, fault-tolerant summary extraction for Studio run cards."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MAX_SUMMARY_BYTES = 1024 * 1024
COUNT_KEYS = (
    "patterns",
    "code_health",
    "permission_risks",
    "typeorm_operations",
    "transaction_correlations",
    "queue_reliability_risks",
)


def _read_small_json(
    root: Path,
    relative_path: str,
    warnings: list[str],
    availability: dict[str, str] | None = None,
) -> dict | list | None:
    path = root.joinpath(*Path(relative_path).parts)
    if not path.is_file():
        if availability is not None:
            availability[relative_path] = "not_generated"
        return None
    try:
        if path.stat().st_size > MAX_SUMMARY_BYTES:
            warnings.append(f"{relative_path} exceeds the Studio summary read limit")
            if availability is not None:
                availability[relative_path] = "malformed"
            return None
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        if availability is not None:
            availability[relative_path] = "available"
        return value
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        warnings.append(f"{relative_path} could not be parsed")
        if availability is not None:
            availability[relative_path] = "malformed"
        return None


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _status(value: Any, allowed: set[str], fallback: str) -> str:
    normalized = str(value or "").lower()
    return normalized if normalized in allowed else fallback


def _count_from(value: Any, key: str) -> int | None:
    try:
        return int(value[key])
    except (KeyError, TypeError, ValueError):
        return None


def _source_status(availability: dict[str, str], *paths: str) -> str:
    states = [availability.get(path, "not_generated") for path in paths]
    if "malformed" in states:
        return "malformed"
    if "available" in states:
        return "available"
    return "not_generated"


def _value(value: Any, status: str) -> dict:
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        normalized = 0
    return {"value": normalized, "availability": status}


def _review_summary(review_report: dict, risk_matrix: dict) -> tuple[str, int | None]:
    review = _as_dict(review_report.get("review_summary"))
    decision = risk_matrix.get("decision") or review.get("decision") or "UNKNOWN"
    human_count = risk_matrix.get("human_review_required_count")
    if human_count is None:
        human_count = review.get("human_review_required_count")
    try:
        return str(decision).upper(), int(human_count) if human_count is not None else None
    except (TypeError, ValueError):
        return str(decision).upper(), None


def _validation_status(validation: dict, evidence: dict, strict: dict) -> str:
    if not validation:
        return "not_available"
    explicit = _status(validation.get("status"), {"pass", "needs_review", "fail"}, "")
    if explicit:
        return explicit
    if validation.get("ready_for_manual_calibration") is True:
        return "pass"
    if validation.get("validation_errors"):
        return "fail"
    if evidence.get("passed") is False or strict.get("passed") is False:
        return "needs_review"
    return "needs_review"


def build_run_summary(run_dir: str) -> dict:
    """Return a compact Studio-only summary without modifying a run directory."""
    root = Path(run_dir)
    warnings: list[str] = []
    availability: dict[str, str] = {}
    read = lambda path: _read_small_json(root, path, warnings, availability)
    review_report = _as_dict(read("repository_review_report.json"))
    risk_matrix = _as_dict(read("review_risk_matrix.json"))
    code_health = _as_dict(read("code_health_summary.json"))
    permission_risks = _as_dict(read("permission_risks.json"))
    authz = _as_dict(read("authz_matrix_diff.json"))
    typeorm = _as_dict(read("typeorm_db_summary.json"))
    aliases = _as_dict(read("typeorm_alias_resolution_summary.json"))
    transactions = _as_dict(read("transaction_correlation_summary.json"))
    reliability = _as_dict(read("queue_reliability_summary.json"))
    patterns = _as_dict(read("pattern_summary.json"))
    quality_gate = _as_dict(read("quality_gate.json"))
    validation = _as_dict(read("validation.json"))
    report = _as_dict(read("report.json"))
    api_surface = _as_dict(read("api_surface.json"))
    cross_language = _as_dict(read("cross_language_links.json"))

    decision, human_count = _review_summary(review_report, risk_matrix)
    evidence = _as_dict(validation.get("evidence_integrity"))
    strict = _as_dict(validation.get("strict_verification"))
    evidence_errors = _as_list(evidence.get("errors"))
    evidence_checked = (
        _count_from(evidence, "checked")
        or _count_from(evidence, "evidence_checked")
        or _count_from(evidence, "total_checked")
        or 0
    )
    if evidence:
        evidence_status = "pass" if evidence.get("passed") is True else "fail" if evidence_errors else "warn"
    else:
        evidence_status = "not_available"
    strict_status = "pass" if strict.get("passed") is True else "fail" if strict else "not_available"
    gate_status = _status(quality_gate.get("status"), {"pass", "warn", "fail"}, "not_available")
    gate_reasons = [
        str(item.get("hint") or item.get("metric") or item.get("reason") or "gate violation")
        for item in _as_list(quality_gate.get("violations"))[:3]
        if isinstance(item, dict)
    ]
    if not gate_reasons:
        gate_reasons = [str(reason) for reason in _as_list(quality_gate.get("hints"))[:3]]

    count_sources = {
        "patterns": _count_from(patterns, "total_patterns"),
        "code_health": _count_from(code_health, "total_findings"),
        "permission_risks": len(_as_list(permission_risks.get("risks"))) if permission_risks else None,
        "typeorm_operations": _count_from(typeorm, "total_operations"),
        "transaction_correlations": _count_from(transactions, "total_correlations"),
        "queue_reliability_risks": _count_from(reliability, "actionable_suspected_risks"),
    }
    counts = {key: int(value or 0) for key, value in count_sources.items()}
    count_availability = {
        key: "available" if count_sources[key] is not None else "not_available"
        for key in COUNT_KEYS
    }
    review_queue = _as_dict(review_report.get("queue_cache_review"))
    backend_counts = _as_dict(review_queue.get("backend_event_counts"))
    review_permission = _as_dict(review_report.get("permission_review"))
    review_code_health = _as_dict(review_report.get("code_health_review"))
    transaction_counts = _as_dict(transactions.get("counts_by_coverage_status"))
    authz_summary = _as_dict(authz.get("summary"))
    api_status = _source_status(availability, "api_surface.json")
    review_status = _source_status(availability, "repository_review_report.json")
    tx_status = _source_status(availability, "transaction_correlation_summary.json")
    typeorm_status = _source_status(availability, "typeorm_db_summary.json")
    queue_status = _source_status(availability, "queue_reliability_summary.json")
    permission_status = _source_status(availability, "permission_risks.json", "authz_matrix_diff.json")
    health_status = _source_status(availability, "code_health_summary.json")
    pattern_status = _source_status(availability, "pattern_summary.json")

    endpoints = len(_as_list(api_surface.get("endpoints"))) if api_status == "available" else 0
    cross_links_value = cross_language.get("links")
    cross_links = len(cross_links_value) if isinstance(cross_links_value, list) else 0
    permission_total = len(_as_list(permission_risks.get("risks"))) if permission_risks else 0
    health_severity = _as_dict(code_health.get("counts_by_severity"))
    health_score = _as_dict(code_health.get("health_score"))
    queue_dispatch = int(backend_counts.get("queue.dispatch") or 0)
    queue_consumers = int(backend_counts.get("queue.consume") or 0)
    cache_operations = sum(int(backend_counts.get(key) or 0) for key in (
        "cache.read", "cache.write", "cache.invalidate"
    ))
    db_reads = int(backend_counts.get("db.read") or typeorm.get("db_reads") or 0)
    db_writes = int(backend_counts.get("db.write") or typeorm.get("db_writes") or 0)
    repository_facts = {
        "api_endpoints": _value(endpoints, api_status),
        "db_reads": _value(db_reads, review_status if review_report else typeorm_status),
        "db_writes": _value(db_writes, review_status if review_report else typeorm_status),
        "transaction_correlations": _value(transactions.get("total_correlations"), tx_status),
        "queue_dispatch": _value(queue_dispatch, review_status),
        "queue_consumers": _value(queue_consumers, review_status),
        "cache_operations": _value(cache_operations, review_status),
        "permission_risks": _value(permission_total, permission_status),
        "code_health_findings": _value(code_health.get("total_findings"), health_status),
    }
    domain_summaries = {
        "architecture": {
            "availability": api_status,
            "api_endpoints": endpoints,
            "cross_language_links": cross_links,
        },
        "transactions": {
            "availability": tx_status,
            "db_reads": db_reads,
            "db_writes": db_writes,
            "total_correlations": int(transactions.get("total_correlations") or 0),
            "covered": int(transaction_counts.get("covered_explicit") or 0),
            "uncovered": int(transaction_counts.get("uncovered") or 0),
            "unknown": int(transaction_counts.get("unknown") or 0),
            "typeorm_operations": int(typeorm.get("total_operations") or 0),
            "resolved_aliases": sum(int(aliases.get(key) or 0) for key in (
                "resolved_direct", "resolved_alias", "resolved_reexport", "resolved_barrel",
                "resolved_local_assignment"
            )),
        },
        "queue": {
            "availability": queue_status,
            "dispatch": queue_dispatch,
            "consumers": queue_consumers,
            "matched_channels": int(reliability.get("matched_channels") or 0),
            "cache_operations": cache_operations,
            "retry_risks": int(reliability.get("actionable_suspected_risks") or 0),
        },
        "permission": {
            "availability": permission_status,
            "risks": int(review_permission.get("total_risks") or permission_total),
            "routes": int(review_permission.get("routes") or authz_summary.get("total_routes") or 0),
            "authz_mode": str(authz.get("mode") or "not_available"),
            "missing_auth": int(authz_summary.get("missing_auth") or 0),
            "human_review": len(_as_list(review_permission.get("human_review_risks"))),
        },
        "code_health": {
            "availability": health_status,
            "findings": int(review_code_health.get("total_findings") or code_health.get("total_findings") or 0),
            "high": int(health_severity.get("high") or 0),
            "medium": int(health_severity.get("medium") or 0),
            "score": int(health_score.get("score") or 0),
            "score_available": bool(health_score.get("enabled")),
        },
        "patterns": {
            "availability": pattern_status,
            "total": int(patterns.get("total_patterns") or 0),
        },
    }
    recommended_actions = []
    for action_id, label, artifact_id, relative_path in (
        ("review_human_items", "Review human-required items", "human_review_required", "human_review_required.md"),
        ("inspect_transactions", "Inspect unresolved transaction coverage", "transaction_correlation_summary", "transaction_correlation_summary.json"),
        ("review_permissions", "Review permission risks", "permission_risk_report", "permission_risk_report.md"),
        ("open_context_pack", "Open Context Pack before AI modification", "context_pack_review_readme", "context_pack/REVIEW/README.md"),
        ("open_validation", "Open validation and gate outputs", "quality_gate", "quality_gate.json"),
    ):
        if root.joinpath(*Path(relative_path).parts).is_file():
            recommended_actions.append({
                "action_id": action_id,
                "label": label,
                "artifact_id": artifact_id,
            })
    return {
        "review_decision": decision,
        "human_review_required_count": human_count,
        "human_review_required_status": "available" if human_count is not None else "not_available",
        "evidence_integrity": {
            "status": evidence_status,
            "checked": evidence_checked,
            "errors": len(evidence_errors),
        },
        "strict_verify": {"status": strict_status},
        "quality_gate": {"status": gate_status, "reasons": gate_reasons},
        "validation": {
            "status": _validation_status(validation, evidence, strict),
        },
        "counts": counts,
        "count_availability": count_availability,
        "repository_facts": repository_facts,
        "domain_summaries": domain_summaries,
        "recommended_actions": recommended_actions,
        "artifact_states": availability,
        "warnings": sorted(set(warnings)),
    }
