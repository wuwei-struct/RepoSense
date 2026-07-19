VALID_DECISIONS = {"PASS", "WARN", "REVIEW", "BLOCK"}


def normalize_human_review_item(item):
    x = item if isinstance(item, dict) else {}
    reason = x.get("reason") if isinstance(x.get("reason"), list) else []
    required = x.get("required_decision") if isinstance(x.get("required_decision"), list) else []
    return {
        "path": str(x.get("path") or ""),
        "reason": [str(v) for v in reason if str(v or "").strip()],
        "suggested_reviewer": str(x.get("suggested_reviewer") or "backend owner"),
        "required_decision": [str(v) for v in required if str(v or "").strip()],
        "evidence_refs": x.get("evidence_refs") if isinstance(x.get("evidence_refs"), list) else [],
        "related_patterns": x.get("related_patterns") if isinstance(x.get("related_patterns"), list) else [],
        "related_risks": x.get("related_risks") if isinstance(x.get("related_risks"), list) else [],
    }


def normalize_risk_matrix(obj):
    x = obj if isinstance(obj, dict) else {}
    decision = str(x.get("decision") or "PASS").upper()
    if decision not in VALID_DECISIONS:
        decision = "REVIEW"
    counts = x.get("counts") if isinstance(x.get("counts"), dict) else {}
    return {
        "decision": decision,
        "counts": {
            "high": int(counts.get("high") or 0),
            "medium": int(counts.get("medium") or 0),
            "low": int(counts.get("low") or 0),
            "confirmed": int(counts.get("confirmed") or 0),
            "suspected": int(counts.get("suspected") or 0),
        },
        "top_risks": x.get("top_risks") if isinstance(x.get("top_risks"), list) else [],
        "human_review_required_count": int(x.get("human_review_required_count") or 0),
        "limitations": x.get("limitations") if isinstance(x.get("limitations"), list) else [],
    }


def normalize_review_report(obj):
    x = obj if isinstance(obj, dict) else {}
    return {
        "version": 1,
        "report_type": "repository_review_report",
        "run_dir": str(x.get("run_dir") or ""),
        "sections": x.get("sections") if isinstance(x.get("sections"), list) else [],
        "review_summary": x.get("review_summary") if isinstance(x.get("review_summary"), dict) else {},
        "backend_risk_review": x.get("backend_risk_review") if isinstance(x.get("backend_risk_review"), dict) else {},
        "side_effect_review": x.get("side_effect_review") if isinstance(x.get("side_effect_review"), dict) else {},
        "transaction_review": x.get("transaction_review") if isinstance(x.get("transaction_review"), dict) else {},
        "queue_cache_review": x.get("queue_cache_review") if isinstance(x.get("queue_cache_review"), dict) else {},
        "messaging_reliability_review": x.get("messaging_reliability_review") if isinstance(x.get("messaging_reliability_review"), dict) else {},
        "api_surface_review": x.get("api_surface_review") if isinstance(x.get("api_surface_review"), dict) else {},
        "pattern_risk_review": x.get("pattern_risk_review") if isinstance(x.get("pattern_risk_review"), dict) else {},
        "quality_gate_review": x.get("quality_gate_review") if isinstance(x.get("quality_gate_review"), dict) else {},
        "human_review_required": [normalize_human_review_item(v) for v in (x.get("human_review_required") or [])],
        "code_health_review": x.get("code_health_review") if isinstance(x.get("code_health_review"), dict) else {},
        "permission_review": x.get("permission_review") if isinstance(x.get("permission_review"), dict) else {},
        "context_calibration": x.get("context_calibration") if isinstance(x.get("context_calibration"), dict) else {},
        "limitations": x.get("limitations") if isinstance(x.get("limitations"), list) else [],
        "risk_matrix": normalize_risk_matrix(x.get("risk_matrix") if isinstance(x.get("risk_matrix"), dict) else {}),
        "evidence_index": x.get("evidence_index") if isinstance(x.get("evidence_index"), list) else [],
    }
