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
    by_rule = Counter(r.get("rule_id") for r in risks)
    by_sev = Counter(r.get("severity") for r in risks)
    by_status = Counter(r.get("status") for r in risks)
    return {
        "total_risks": len(risks),
        "counts_by_rule": dict(sorted((k, int(v)) for k, v in by_rule.items() if k)),
        "counts_by_severity": dict(sorted((k, int(v)) for k, v in by_sev.items() if k)),
        "counts_by_status": dict(sorted((k, int(v)) for k, v in by_status.items() if k)),
        "routes": len(routes),
        "write_like_routes": len([r for r in routes if r.get("write_like")]),
        "sensitive_routes": len([r for r in routes if r.get("sensitive")]),
        "frontend_permission_signals": len(frontend),
        "negative_test_gaps": len([r for r in risks if r.get("rule_id") == "AUTHZ-005"]),
        "limitations": LIMITATIONS[:],
    }

