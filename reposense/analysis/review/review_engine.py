import json
import os
import time
from collections import Counter

from ...evidence.location import filter_valid_evidence_refs
from .review_schema import normalize_review_report, normalize_risk_matrix


SECTIONS = [
    "Review Summary",
    "Backend Risk Review",
    "Side-effect Review",
    "Transaction Review",
    "Queue / Cache Review",
    "Messaging Reliability Review",
    "API Surface Review",
    "Pattern Risk Review",
    "Quality Gate Review",
    "Code Health Review",
    "Permission Review",
    "Context Calibration",
    "Human Review Required",
    "Limitations",
]


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _patterns_from_run(run_dir):
    obj = _read_json(os.path.join(run_dir, "patterns.json"), {"patterns": []})
    rows = obj.get("patterns") if isinstance(obj, dict) else []
    return rows if isinstance(rows, list) else []


def _risks_from_run(run_dir, patterns):
    obj = _read_json(os.path.join(run_dir, "ai_risks", "risks.json"), {})
    rows = obj.get("risk_items") if isinstance(obj, dict) else []
    if isinstance(rows, list) and rows:
        return rows
    risks = []
    for p in patterns:
        risks.append(
            {
                "risk_id": "risk-" + str(p.get("pattern_id") or ""),
                "title": str(p.get("title") or p.get("pattern_type") or "pattern risk"),
                "severity": str(p.get("severity") or "medium"),
                "status": str(p.get("status") or "suspected"),
                "pattern_type": str(p.get("pattern_type") or ""),
                "description": str(p.get("summary") or ""),
                "why_it_matters": "Pattern is linked to backend transaction or side-effect review.",
                "evidence_refs": p.get("evidence_refs") if isinstance(p.get("evidence_refs"), list) else [],
                "related_patterns": [str(p.get("pattern_id") or "")],
                "related_findings": [str(x) for x in (p.get("supporting_findings") or [])],
                "related_events": [str(x) for x in (p.get("supporting_events") or [])],
                "recommended_action": str(p.get("explain_stub") or "Review evidence and confirm implementation boundary."),
            }
        )
    return risks


def _severity_rank(sev):
    return {"high": 3, "medium": 2, "low": 1}.get(str(sev or "").lower(), 0)


def _risk_sort_key(r):
    return (-_severity_rank(r.get("severity")), str(r.get("status") or ""), str(r.get("risk_id") or r.get("title") or ""))


def _count_evidence(risk):
    refs = risk.get("evidence_refs")
    return len(refs) if isinstance(refs, list) else 0


def _make_risk_matrix(risks, human_items):
    counts = Counter()
    for r in risks:
        sev = str(r.get("severity") or "low").lower()
        st = str(r.get("status") or "suspected").lower()
        if sev in ("high", "medium", "low"):
            counts[sev] += 1
        if st in ("confirmed", "suspected"):
            counts[st] += 1
    decision = "PASS"
    if any(str(r.get("severity") or "").lower() == "high" and str(r.get("status") or "").lower() == "confirmed" and _count_evidence(r) >= 2 for r in risks):
        decision = "BLOCK"
    elif any(str(r.get("severity") or "").lower() == "high" and str(r.get("status") or "").lower() == "suspected" for r in risks):
        decision = "REVIEW"
    elif any(str(r.get("severity") or "").lower() == "medium" and str(r.get("status") or "").lower() == "confirmed" for r in risks) and counts["medium"] > 1:
        decision = "REVIEW"
    elif counts["medium"] > 0 or counts["low"] > 0 or counts["high"] > 0:
        decision = "WARN"
    top = sorted(risks, key=_risk_sort_key)[:5]
    return normalize_risk_matrix(
        {
            "decision": decision,
            "counts": dict(counts),
            "top_risks": [
                {
                    "risk_id": str(x.get("risk_id") or ""),
                    "title": str(x.get("title") or ""),
                    "severity": str(x.get("severity") or ""),
                    "status": str(x.get("status") or ""),
                    "pattern_type": str(x.get("pattern_type") or ""),
                    "evidence_count": _count_evidence(x),
                }
                for x in top
            ],
            "human_review_required_count": len(human_items),
            "limitations": [
                "Decision is conservative and evidence-guided.",
                "Decision is not a guarantee of backend safety or correctness.",
            ],
        }
    )


def _reason_for_pattern(pattern_type):
    pt = str(pattern_type or "")
    if pt in ("transaction_missing", "db_write_outside_tx"):
        return ["DB write found", "transaction evidence missing"]
    if pt == "queue_without_consumer":
        return ["queue dispatch found", "consumer evidence missing"]
    if pt == "queue_retry_without_idempotency_guard":
        return [
            "explicit queue retry found",
            "consumer side effect found",
            "consumer idempotency evidence not observed",
        ]
    if pt == "queue_consumer_side_effect_without_idempotency_evidence":
        return [
            "matched consumer side effect found",
            "retry policy unresolved",
            "consumer idempotency evidence not observed",
        ]
    if pt == "api_write_without_idempotency_guard":
        return ["write path found", "idempotency guard not found"]
    if pt in ("hot_write_path", "complex_write_path"):
        return ["multiple side-effect signals found", "write path complexity is elevated"]
    return ["evidence-linked backend risk found"]


def _decision_questions(pattern_type):
    pt = str(pattern_type or "")
    if pt in ("transaction_missing", "db_write_outside_tx"):
        return ["Should this operation be transactional?", "Should this path require further tests?"]
    if pt == "queue_without_consumer":
        return ["Should this queue have a consumer?", "Should this path require further tests?"]
    if pt in {
        "queue_retry_without_idempotency_guard",
        "queue_consumer_side_effect_without_idempotency_evidence",
    }:
        return [
            "Can this consumer process the same delivery more than once?",
            "Where is the persistent or atomic idempotency guard?",
            "Which duplicate-delivery tests are required?",
        ]
    if pt == "api_write_without_idempotency_guard":
        return ["Should duplicate submission be rejected?", "Should this path require further tests?"]
    return ["Should this path require further tests?"]


def _make_human_items(risks):
    items = []
    seen = set()
    skipped = 0
    for risk in sorted(risks, key=_risk_sort_key):
        refs, invalid_ref_count = filter_valid_evidence_refs(risk.get("evidence_refs"))
        skipped += invalid_ref_count
        if not refs:
            continue
        pattern_type = str(risk.get("pattern_type") or "")
        path = ""
        for ref in refs:
            path = str(ref.get("file") or ref.get("path") or "")
            if path:
                break
        key = (path, str(risk.get("risk_id") or ""))
        if key in seen:
            continue
        seen.add(key)
        items.append(
            {
                "path": path or "(artifact evidence)",
                "reason": _reason_for_pattern(pattern_type),
                "suggested_reviewer": "backend owner",
                "required_decision": _decision_questions(pattern_type),
                "evidence_refs": refs[:5],
                "related_patterns": risk.get("related_patterns") if isinstance(risk.get("related_patterns"), list) else [],
                "related_risks": [str(risk.get("risk_id") or "")],
                "_invalid_evidence_refs_skipped": invalid_ref_count,
            }
        )
        if len(items) >= 20:
            break
    return items, skipped


def _decision_questions_for_health(rule_id):
    rid = str(rule_id or "")
    if rid == "CHD-001":
        return ["Should this file be split?", "Should ownership or module boundaries be clarified?"]
    if rid == "CHD-003":
        return ["Should this type escape be removed?", "Should this path require stronger type coverage?"]
    if rid == "CHD-004":
        return ["Should this error be logged or re-thrown?", "Should this failure path have tests?"]
    if rid == "CHD-005":
        return ["Should this backend side-effect path have tests?", "Should this operation require transaction/idempotency review?"]
    return ["Should this maintainability risk be accepted or fixed?"]


def _make_health_human_items(maintainability_risks):
    obj = maintainability_risks if isinstance(maintainability_risks, dict) else {}
    risks = obj.get("risks") if isinstance(obj.get("risks"), list) else []
    items = []
    skipped = 0
    for risk in risks:
        sev = str(risk.get("severity") or "").lower()
        if not bool(risk.get("suggested_human_review", True)):
            continue
        if sev not in ("high", "medium"):
            continue
        rid = str(risk.get("rule_id") or "")
        path = str(risk.get("file") or "")
        refs, invalid_ref_count = filter_valid_evidence_refs(risk.get("evidence_refs"))
        skipped += invalid_ref_count
        if not refs:
            continue
        items.append(
            {
                "path": path or "(code health evidence)",
                "reason": [str(risk.get("reason") or "Code health maintainability risk observed."), str(risk.get("title") or rid)],
                "suggested_reviewer": "backend owner",
                "required_decision": _decision_questions_for_health(rid),
                "evidence_refs": refs,
                "related_patterns": [],
                "related_risks": [str(risk.get("risk_id") or "")],
                "_invalid_evidence_refs_skipped": invalid_ref_count,
            }
        )
        if len(items) >= 20:
            break
    return items, skipped


def _make_permission_human_items(permission_risks, matrix_diff=None):
    obj = permission_risks if isinstance(permission_risks, dict) else {}
    risks = obj.get("risks") if isinstance(obj.get("risks"), list) else []
    items = []
    skipped = 0
    for risk in risks:
        if str(risk.get("severity") or "").lower() not in ("high", "medium"):
            continue
        route = risk.get("route") if isinstance(risk.get("route"), dict) else {}
        label = (str(route.get("method") or "") + " " + str(route.get("path") or "")).strip()
        refs, invalid_ref_count = filter_valid_evidence_refs(risk.get("evidence_refs"))
        skipped += invalid_ref_count
        if not refs:
            continue
        items.append(
            {
                "path": str(risk.get("file") or label or "(permission evidence)"),
                "reason": [str(risk.get("reason") or "Permission risk observed."), str(risk.get("title") or risk.get("rule_id") or "")],
                "suggested_reviewer": "backend/security owner",
                "required_decision": [
                    "Should this route require authentication?",
                    "Should this route require role or permission checks?",
                    "Should this route have negative authorization tests?",
                ],
                "evidence_refs": refs,
                "related_patterns": [],
                "related_risks": [str(risk.get("risk_id") or "")],
                "_invalid_evidence_refs_skipped": invalid_ref_count,
            }
        )
        if len(items) >= 20:
            break
    md = matrix_diff if isinstance(matrix_diff, dict) else {}
    for diff in md.get("diffs") or []:
        if str(diff.get("severity") or "").lower() not in ("high", "medium"):
            continue
        route = diff.get("route") if isinstance(diff.get("route"), dict) else {}
        label = (str(route.get("method") or "") + " " + str(route.get("path") or "")).strip()
        refs, invalid_ref_count = filter_valid_evidence_refs(diff.get("evidence_refs"))
        skipped += invalid_ref_count
        if not refs:
            continue
        items.append(
            {
                "path": label or "(authz matrix diff)",
                "reason": [str(diff.get("reason") or "AuthZ Matrix expected signal not observed."), ",".join(diff.get("missing") or [])],
                "suggested_reviewer": "backend/security owner",
                "required_decision": diff.get("suggested_human_decision") if isinstance(diff.get("suggested_human_decision"), list) else ["Confirm expected permission contract and enforcement location."],
                "evidence_refs": refs,
                "related_patterns": [],
                "related_risks": [str(diff.get("diff_id") or "")],
                "_invalid_evidence_refs_skipped": invalid_ref_count,
            }
        )
        if len(items) >= 40:
            break
    return items, skipped


def _human_item_key(item):
    refs = item.get("evidence_refs") if isinstance(item.get("evidence_refs"), list) else []
    first = refs[0] if refs and isinstance(refs[0], dict) else {}
    source_ids = tuple(sorted(str(x) for x in (item.get("related_risks") or item.get("related_patterns") or []) if str(x)))
    decisions = tuple(sorted(str(x) for x in (item.get("required_decision") or []) if str(x)))
    return (
        source_ids,
        str(first.get("file") or item.get("path") or ""),
        int(first.get("start_line") or 0),
        int(first.get("end_line") or 0),
        decisions,
    )


def _dedupe_human_items(items):
    deduped = []
    seen = set()
    for item in items:
        key = _human_item_key(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _code_health_review(code_health, summary, maintainability_risks):
    if not isinstance(code_health, dict) or not code_health:
        return {
            "status": "planned",
            "note": "Not available in this run. Generate it with reposense health scan <run_dir> --repo <repo_path>.",
        }
    findings = code_health.get("findings") if isinstance(code_health.get("findings"), list) else []
    risks = (maintainability_risks.get("risks") if isinstance(maintainability_risks, dict) else []) or []
    high_medium = [r for r in risks if str(r.get("severity") or "").lower() in ("high", "medium")]
    return {
        "status": "enabled",
        "total_findings": int(summary.get("total_findings") or len(findings)) if isinstance(summary, dict) else len(findings),
        "raw_findings": int(summary.get("raw_findings") or len(findings)) if isinstance(summary, dict) else len(findings),
        "actionable_findings": int(summary.get("actionable_findings") or len(high_medium)) if isinstance(summary, dict) else len(high_medium),
        "findings_downweighted": int(summary.get("findings_downweighted") or 0) if isinstance(summary, dict) else 0,
        "findings_excluded_from_primary_review": int(summary.get("findings_excluded_from_primary_review") or 0) if isinstance(summary, dict) else 0,
        "counts_by_rule": summary.get("counts_by_rule") if isinstance(summary.get("counts_by_rule"), dict) else {},
        "counts_by_severity": summary.get("counts_by_severity") if isinstance(summary.get("counts_by_severity"), dict) else {},
        "health_score": summary.get("health_score") if isinstance(summary.get("health_score"), dict) else {},
        "human_review_risks": high_medium[:10],
        "limitations": code_health.get("limitations") if isinstance(code_health.get("limitations"), list) else [],
    }


def _permission_review(
    permission_surface,
    permission_risks,
    matrix_diff=None,
    guard_summary=None,
):
    if not isinstance(permission_surface, dict) or not permission_surface:
        return {
            "status": "planned",
            "note": "Not available in this run. Generate it with reposense authz scan <run_dir> --repo <repo_path>.",
        }
    risks = permission_risks.get("risks") if isinstance(permission_risks.get("risks"), list) else []
    routes = permission_surface.get("routes") if isinstance(permission_surface.get("routes"), list) else []
    frontend = permission_surface.get("frontend_permission_signals") if isinstance(permission_surface.get("frontend_permission_signals"), list) else []
    counts = Counter(str(r.get("severity") or "low").lower() for r in risks)
    by_rule = Counter(str(r.get("rule_id") or "") for r in risks)
    actionable = [
        r
        for r in risks
        if bool(r.get("suggested_human_review", True))
        and str(r.get("severity") or "").lower() in ("high", "medium")
    ]
    md = matrix_diff if isinstance(matrix_diff, dict) else {}
    msm = md.get("summary") if isinstance(md.get("summary"), dict) else {}
    guards = guard_summary if isinstance(guard_summary, dict) else {}
    return {
        "status": "enabled",
        "total_risks": len(risks),
        "raw_risks": len(risks),
        "actionable_risks": len(actionable),
        "counts_by_severity": dict(sorted(counts.items())),
        "counts_by_rule": dict(sorted((k, int(v)) for k, v in by_rule.items() if k)),
        "routes": len(routes),
        "frontend_permission_signals": len(frontend),
        "negative_test_gaps": len([r for r in risks if r.get("rule_id") == "AUTHZ-005"]),
        "public_auth_entrypoints": len([r for r in routes if r.get("intent") == "public_auth_entrypoint"]),
        "authz_matrix": {
            "mode": str(md.get("mode") or ""),
            "missing_auth": int(msm.get("missing_auth") or 0),
            "missing_permission": int(msm.get("missing_permission") or 0),
            "missing_ownership_check": int(msm.get("missing_ownership_check") or 0),
            "missing_tenant_boundary": int(msm.get("missing_tenant_boundary") or 0),
            "missing_transaction": int(msm.get("missing_transaction") or 0),
            "missing_audit_log": int(msm.get("missing_audit_log") or 0),
        } if md else {},
        "guard_correlation": {
            "status": "enabled" if guards else "not_available",
            "protected_method": int(guards.get("protected_method") or 0),
            "protected_controller": int(guards.get("protected_controller") or 0),
            "protected_global": int(guards.get("protected_global") or 0),
            "intentional_public_bypasses": int(
                guards.get("intentional_public_bypasses") or 0
            ),
            "openapi_protected_without_code_guard": int(
                guards.get("openapi_protected_without_code_guard") or 0
            ),
            "openapi_only_routes": int(guards.get("openapi_only_routes") or 0),
            "unresolved_routes": int(guards.get("unknown_routes") or 0)
            + int(guards.get("ambiguous_routes") or 0),
        },
        "human_review_risks": actionable[:10],
        "limitations": permission_risks.get("limitations") if isinstance(permission_risks.get("limitations"), list) else [],
    }


def _event_counts(event_graph):
    nodes = event_graph.get("nodes") if isinstance(event_graph.get("nodes"), list) else []
    c = Counter(str(n.get("type") or "unknown") for n in nodes)
    return dict(sorted(c.items()))


def generate_repository_review(run_dir):
    backend = _read_json(os.path.join(run_dir, "backend_verifier_report.json"), {})
    patterns = _patterns_from_run(run_dir)
    psummary = _read_json(os.path.join(run_dir, "pattern_summary.json"), {})
    risks = _risks_from_run(run_dir, patterns)
    gate = _read_json(os.path.join(run_dir, "quality_gate.json"), {})
    graph = _read_json(os.path.join(run_dir, "event_graph.json"), {})
    api_surface = _read_json(os.path.join(run_dir, "api_surface.json"), {})
    code_health = _read_json(os.path.join(run_dir, "code_health.json"), {})
    code_health_summary = _read_json(os.path.join(run_dir, "code_health_summary.json"), {})
    maintainability_risks = _read_json(os.path.join(run_dir, "maintainability_risks.json"), {})
    permission_surface = _read_json(os.path.join(run_dir, "permission_surface.json"), {})
    permission_risks = _read_json(os.path.join(run_dir, "permission_risks.json"), {})
    authz_matrix_diff = _read_json(os.path.join(run_dir, "authz_matrix_diff.json"), {})
    transaction_correlation_summary = _read_json(os.path.join(run_dir, "transaction_correlation_summary.json"), {})
    typescript_transaction_summary = (
        transaction_correlation_summary.get("by_language_framework") or {}
    ).get("typescript/typeorm") or {}
    review_context_summary = _read_json(os.path.join(run_dir, "review_context_summary.json"), {})
    route_guard_summary = _read_json(
        os.path.join(run_dir, "route_guard_summary.json"), {}
    )
    route_decorator_summary = _read_json(
        os.path.join(run_dir, "route_decorator_summary.json"), {}
    )
    queue_cache_validation = _read_json(
        os.path.join(run_dir, "queue_cache_validation.json"), {}
    )
    typeorm_db_summary = _read_json(
        os.path.join(run_dir, "typeorm_db_summary.json"), {}
    )
    queue_reliability_summary = _read_json(
        os.path.join(run_dir, "queue_reliability_summary.json"), {}
    )
    queue_reliability_risks = _read_json(
        os.path.join(run_dir, "queue_reliability_risks.json"), {}
    )

    human_items, backend_skipped = _make_human_items(risks)
    health_items, health_skipped = _make_health_human_items(maintainability_risks)
    permission_items, permission_skipped = _make_permission_human_items(permission_risks, authz_matrix_diff)
    human_items.extend(health_items)
    human_items.extend(permission_items)
    skipped_invalid_evidence = backend_skipped + health_skipped + permission_skipped
    human_items = _dedupe_human_items(human_items)
    risk_matrix = _make_risk_matrix(risks, human_items)
    backend_events = backend.get("backend_events_summary") if isinstance(backend.get("backend_events_summary"), dict) else {}
    tx = backend.get("transaction_signals") if isinstance(backend.get("transaction_signals"), dict) else {}
    side_effect = backend.get("side_effect_map") if isinstance(backend.get("side_effect_map"), dict) else {}

    return normalize_review_report(
        {
            "run_dir": run_dir,
            "sections": SECTIONS[:],
            "review_summary": {
                "decision": risk_matrix["decision"],
                "total_risks": len(risks),
                "human_review_required_count": len(human_items),
                "gate_status": str(gate.get("status") or "n/a"),
                "generated_at": int(time.time()),
                "mode": "evidence_guided_repository_review",
            },
            "backend_risk_review": {
                "top_risks": risk_matrix["top_risks"],
                "backend_verifier_available": bool(backend),
            },
            "side_effect_review": {
                "mode": str(side_effect.get("mode") or "conservative_side_effect_map"),
                "paths": side_effect.get("paths") if isinstance(side_effect.get("paths"), list) else [],
            },
            "transaction_review": {
                **tx,
                "correlation_status": "enabled" if transaction_correlation_summary else "not_available",
                "transaction_correlations": transaction_correlation_summary,
                "typescript_typeorm_correlations": {
                    "status": (
                        "enabled"
                        if typescript_transaction_summary
                        else "not_available"
                    ),
                    **typescript_transaction_summary,
                },
                "typeorm_db_coverage": {
                    "status": "enabled" if typeorm_db_summary else "not_available",
                    **typeorm_db_summary,
                },
            },
            "queue_cache_review": {
                "backend_event_counts": backend_events.get("counts") if isinstance(backend_events.get("counts"), dict) else _event_counts(graph),
                "validation_status": "enabled" if queue_cache_validation else "not_available",
                "validation_summary": (
                    queue_cache_validation.get("summary")
                    if isinstance(queue_cache_validation.get("summary"), dict)
                    else {}
                ),
            },
            "messaging_reliability_review": {
                "status": (
                    "enabled"
                    if queue_reliability_summary
                    else "not_available"
                ),
                **queue_reliability_summary,
                "actionable_suspected_risks": len(
                    queue_reliability_risks.get("risks") or []
                ),
            },
            "api_surface_review": {
                "api_total": int(((api_surface.get("stats") or {}).get("unique_endpoints")) or len(api_surface.get("endpoints") or [])),
                "openapi_present": bool((((api_surface.get("stats") or {}).get("by_source_kind") or {}).get("openapi") or 0) > 0),
                "route_decorator_classification": {
                    "status": "enabled" if route_decorator_summary else "not_available",
                    "candidate_count": int(route_decorator_summary.get("candidate_count") or 0),
                    "accepted_route_count": int(route_decorator_summary.get("accepted_route_count") or 0),
                    "rejected_non_route_count": int(route_decorator_summary.get("rejected_non_route_count") or 0),
                    "unknown_count": int(route_decorator_summary.get("unknown_count") or 0),
                },
            },
            "pattern_risk_review": {
                "total_patterns": int(psummary.get("total_patterns") or len(patterns)),
                "counts_by_type": psummary.get("counts_by_type") if isinstance(psummary.get("counts_by_type"), dict) else {},
                "counts_by_severity": psummary.get("counts_by_severity") if isinstance(psummary.get("counts_by_severity"), dict) else {},
                "counts_by_status": psummary.get("counts_by_status") if isinstance(psummary.get("counts_by_status"), dict) else {},
            },
            "quality_gate_review": {
                "status": str(gate.get("status") or "n/a"),
                "violations": gate.get("violations") if isinstance(gate.get("violations"), list) else [],
            },
            "human_review_required": human_items,
            "code_health_review": _code_health_review(code_health, code_health_summary, maintainability_risks),
            "permission_review": _permission_review(
                permission_surface,
                permission_risks,
                authz_matrix_diff,
                route_guard_summary,
            ),
            "context_calibration": {
                "status": "enabled" if review_context_summary else "not_available",
                **review_context_summary,
                "raw_code_health_findings": len(code_health.get("findings") or []),
                "actionable_code_health_risks": len(maintainability_risks.get("risks") or []),
                "raw_permission_risks": len(permission_risks.get("risks") or []),
                "actionable_permission_risks": len(
                    [
                        risk
                        for risk in (permission_risks.get("risks") or [])
                        if bool(risk.get("suggested_human_review", True))
                        and str(risk.get("severity") or "").lower() in ("high", "medium")
                    ]
                ),
            },
            "limitations": [
                "Evidence-guided repository review only.",
                "Does not replace human code review.",
                "Does not guarantee backend safety.",
                "Does not prove all transactions are correct.",
                "Uses existing run artifacts only; no new scanning or unrestricted source browsing is performed.",
                "Code Health Review is enabled only when code_health artifacts exist.",
                "Permission Review is enabled only when permission artifacts exist.",
                "Queue reliability correlation does not prove runtime retry or consumer idempotency.",
            ] + ([f"Skipped {skipped_invalid_evidence} invalid evidence reference(s) during review aggregation."] if skipped_invalid_evidence else []),
            "risk_matrix": risk_matrix,
            "evidence_index": (backend.get("evidence_index") if isinstance(backend.get("evidence_index"), list) else [])[:50],
        }
    )
