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


def _read_small_json(root: Path, relative_path: str, warnings: list[str]) -> dict | list | None:
    path = root.joinpath(*Path(relative_path).parts)
    if not path.is_file():
        return None
    try:
        if path.stat().st_size > MAX_SUMMARY_BYTES:
            warnings.append(f"{relative_path} exceeds the Studio summary read limit")
            return None
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        warnings.append(f"{relative_path} could not be parsed")
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
    review_report = _as_dict(_read_small_json(root, "repository_review_report.json", warnings))
    risk_matrix = _as_dict(_read_small_json(root, "review_risk_matrix.json", warnings))
    code_health = _as_dict(_read_small_json(root, "code_health_summary.json", warnings))
    permission_risks = _as_dict(_read_small_json(root, "permission_risks.json", warnings))
    typeorm = _as_dict(_read_small_json(root, "typeorm_db_summary.json", warnings))
    transactions = _as_dict(_read_small_json(root, "transaction_correlation_summary.json", warnings))
    reliability = _as_dict(_read_small_json(root, "queue_reliability_summary.json", warnings))
    patterns = _as_dict(_read_small_json(root, "pattern_summary.json", warnings))
    quality_gate = _as_dict(_read_small_json(root, "quality_gate.json", warnings))
    validation = _as_dict(_read_small_json(root, "validation.json", warnings))

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
        "warnings": sorted(set(warnings)),
    }
