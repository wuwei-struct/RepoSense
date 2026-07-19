import yaml


def infer_authz_matrix(permission_surface, permission_risks):
    routes = permission_surface.get("routes") if isinstance(permission_surface.get("routes"), list) else []
    risks = permission_risks.get("risks") if isinstance(permission_risks.get("risks"), list) else []
    risk_by_route = {}
    for r in risks:
        route = r.get("route") if isinstance(r.get("route"), dict) else {}
        risk_by_route.setdefault((route.get("method"), route.get("path")), []).append(r)
    out_routes = {}
    for r in routes:
        key = f"{r.get('method')} {r.get('path')}".strip()
        related = risk_by_route.get((r.get("method"), r.get("path")), [])
        out_routes[key] = {
            "resource": "",
            "action": "",
            "inferred": True,
            "confidence": 0.55 if related else 0.45,
            "needs_confirmation": True,
            "observed": {
                "auth_signals": r.get("auth_signals") or [],
                "role_permission_signals": r.get("role_permission_signals") or [],
                "effective_auth_status": str(
                    r.get("effective_auth_status") or "unknown"
                ),
                "guard_scope": str(r.get("guard_scope") or ""),
                "effective_role_status": str(
                    r.get("effective_role_status") or "unknown"
                ),
                "public_bypass": bool(r.get("public_bypass")),
                "openapi_security_expectation": str(
                    r.get("openapi_security_expectation") or "not_available"
                ),
                "guard_correlation_confidence": float(
                    r.get("guard_correlation_confidence") or 0.0
                ),
                "write_like": bool(r.get("write_like")),
                "sensitive": bool(r.get("sensitive")),
                "route_intent": str(r.get("intent") or "unknown"),
                "route_intent_confidence": float(r.get("intent_confidence") or 0.0),
            },
            "evidence_refs": r.get("source_refs") or [],
        }
    return {
        "version": "authz_matrix_inferred_v1",
        "inferred": True,
        "note": "This inferred matrix is not an authority contract. It is a review aid and must be confirmed by the project owner.",
        "routes": out_routes,
    }


def render_inferred_yaml(obj):
    return yaml.safe_dump(obj, sort_keys=True, allow_unicode=True)
