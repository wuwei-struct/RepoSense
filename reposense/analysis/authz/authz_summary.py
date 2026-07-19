from collections import Counter


LIMITATIONS = [
    "Permission Auditor MVP uses conservative static text and artifact matching.",
    "It does not prove authorization correctness.",
    "It does not build a complete AuthZ Matrix in this release.",
    "Negative permission test gaps are inferred from file names and keywords only.",
    "Frontend-only permission risks are suspected unless backend route correspondence is explicit.",
]


def summarize_permission(surface, risks):
    routes = surface.get("routes") if isinstance(surface.get("routes"), list) else []
    frontend = surface.get("frontend_permission_signals") if isinstance(surface.get("frontend_permission_signals"), list) else []
    guard_summary = surface.get("route_guard_summary") if isinstance(surface.get("route_guard_summary"), dict) else {}
    by_rule = Counter(r.get("rule_id") for r in risks)
    by_sev = Counter(r.get("severity") for r in risks)
    by_status = Counter(r.get("status") for r in risks)
    return {
        "total_risks": len(risks),
        "actionable_risks": len(
            [
                r
                for r in risks
                if bool(r.get("suggested_human_review", True))
                and str(r.get("severity") or "").lower() in {"high", "medium"}
            ]
        ),
        "counts_by_rule": dict(sorted((k, int(v)) for k, v in by_rule.items() if k)),
        "counts_by_severity": dict(sorted((k, int(v)) for k, v in by_sev.items() if k)),
        "counts_by_status": dict(sorted((k, int(v)) for k, v in by_status.items() if k)),
        "routes": len(routes),
        "write_like_routes": len([r for r in routes if r.get("write_like")]),
        "sensitive_routes": len([r for r in routes if r.get("sensitive")]),
        "frontend_permission_signals": len(frontend),
        "negative_test_gaps": len([r for r in risks if r.get("rule_id") == "AUTHZ-005"]),
        "public_auth_entrypoints": len(
            [r for r in routes if r.get("intent") == "public_auth_entrypoint"]
        ),
        "protected_auth_operations": len(
            [r for r in routes if r.get("intent") == "protected_auth_operation"]
        ),
        "route_guard_correlation": {
            "protected_method": int(guard_summary.get("protected_method") or 0),
            "protected_controller": int(guard_summary.get("protected_controller") or 0),
            "protected_global": int(guard_summary.get("protected_global") or 0),
            "intentional_public_bypasses": int(
                guard_summary.get("intentional_public_bypasses") or 0
            ),
            "openapi_protected_without_code_guard": int(
                guard_summary.get("openapi_protected_without_code_guard") or 0
            ),
            "openapi_only_routes": int(guard_summary.get("openapi_only_routes") or 0),
            "unknown_routes": int(guard_summary.get("unknown_routes") or 0),
        },
        "limitations": LIMITATIONS[:],
    }
