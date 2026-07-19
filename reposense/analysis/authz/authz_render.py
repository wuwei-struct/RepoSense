def render_permission_risk_report(surface, risks_payload, summary):
    risks = risks_payload.get("risks") if isinstance(risks_payload.get("risks"), list) else []
    actionable_risks = [risk for risk in risks if bool(risk.get("suggested_human_review", True))]
    lines = [
        "# Permission Risk Report",
        "",
        "## Summary",
        f"- Total risks: {int(summary.get('total_risks') or 0)}",
        f"- Routes: {int(summary.get('routes') or 0)}",
        f"- Write-like routes: {int(summary.get('write_like_routes') or 0)}",
        f"- Sensitive routes: {int(summary.get('sensitive_routes') or 0)}",
        f"- Frontend permission signals: {int(summary.get('frontend_permission_signals') or 0)}",
        "",
        "## Permission Surface",
    ]
    for r in (surface.get("routes") or [])[:20]:
        lines.append(f"- {r.get('method')} {r.get('path')} @ {r.get('file')}:{r.get('line_start')} auth={len(r.get('auth_signals') or [])} role={len(r.get('role_permission_signals') or [])}")
    lines += ["", "## High-risk Permission Findings"]
    for r in [x for x in actionable_risks if x.get("severity") == "high"][:20]:
        lines.append(f"- [{r.get('status')}] {r.get('rule_id')} {r.get('route', {}).get('method')} {r.get('route', {}).get('path')} @ {r.get('file')}:{r.get('line_start')}")
    lines += ["", "## Frontend-only Permission Signals"]
    for s in (surface.get("frontend_permission_signals") or [])[:20]:
        lines.append(f"- {s.get('file')}:{s.get('line_start')} {', '.join(s.get('signals') or [])}")
    lines += ["", "## Negative Test Gaps"]
    for r in [x for x in risks if x.get("rule_id") == "AUTHZ-005"][:20]:
        lines.append(f"- {r.get('route', {}).get('method')} {r.get('route', {}).get('path')} @ {r.get('file')}")
    lines += ["", "## Human Permission Review Required"]
    for r in [x for x in actionable_risks if x.get("severity") in ("high", "medium")][:20]:
        lines.append(f"- {r.get('rule_id')} {r.get('title')} @ {r.get('file')}:{r.get('line_start')}")
    lines += ["", "## Limitations"]
    for item in risks_payload.get("limitations") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def render_human_permission_review(risks_payload):
    risks = [
        r
        for r in (risks_payload.get("risks") or [])
        if r.get("severity") in ("high", "medium") and bool(r.get("suggested_human_review", True))
    ]
    lines = ["# Human Permission Review Required", ""]
    if not risks:
        lines.append("No medium/high permission review items were generated.")
        lines.append("")
        return "\n".join(lines)
    for idx, r in enumerate(risks, 1):
        route = r.get("route") or {}
        lines.append(f"## {idx}. {route.get('method')} {route.get('path')}")
        lines.append("")
        lines.append(f"- file: {r.get('file')}:{r.get('line_start')}")
        lines.append(f"- reason: {r.get('reason')}")
        lines.append("- suggested reviewer: backend/security owner")
        lines.append("- required decision:")
        lines.append("  - Should this route require authentication?")
        lines.append("  - Should this route require role or permission checks?")
        lines.append("  - Should this route have negative authorization tests?")
        lines.append("")
    return "\n".join(lines)


def render_negative_test_plan(risks_payload):
    risks = [r for r in (risks_payload.get("risks") or []) if r.get("rule_id") in {"AUTHZ-001", "AUTHZ-002", "AUTHZ-003", "AUTHZ-005"}]
    seen = set()
    lines = ["# AuthZ Negative Test Plan", ""]
    for r in risks:
        route = r.get("route") or {}
        key = (route.get("method"), route.get("path"), r.get("file"))
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"## {route.get('method')} {route.get('path')}")
        lines.append("")
        if "public_auth_entrypoint" in (r.get("signals") or []):
            lines.append("- invalid credentials -> expected authentication failure")
            lines.append("- disabled account -> expected authentication failure")
            lines.append("- malformed request -> expected validation failure")
            lines.append("- invalid reset or verification token -> expected safe failure when applicable")
            lines.append("- abuse or rate-limit behavior -> requires project-owner confirmation")
        else:
            lines.append("- anonymous user -> 401")
            lines.append("- authenticated user without permission -> 403")
            lines.append("- wrong role -> 403")
            lines.append("- owner mismatch -> 403")
            lines.append("- tenant mismatch -> 403")
            lines.append("- duplicate sensitive operation -> expected safe failure")
        lines.append("")
    if not seen:
        lines.append("No permission-sensitive routes were selected for negative test suggestions.")
        lines.append("")
    return "\n".join(lines)
