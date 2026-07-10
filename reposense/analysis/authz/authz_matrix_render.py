def render_matrix_report(loaded, inferred, diff):
    summary = diff.get("summary") or {}
    lines = [
        "# AuthZ Matrix Report",
        "",
        "## Summary",
        f"- Mode: {diff.get('mode')}",
        f"- Total routes: {int(summary.get('total_routes') or 0)}",
        f"- Matched routes: {int(summary.get('matched_routes') or 0)}",
        f"- Missing auth: {int(summary.get('missing_auth') or 0)}",
        f"- Missing permission: {int(summary.get('missing_permission') or 0)}",
        f"- Missing ownership check: {int(summary.get('missing_ownership_check') or 0)}",
        f"- Missing tenant boundary: {int(summary.get('missing_tenant_boundary') or 0)}",
        f"- Missing transaction: {int(summary.get('missing_transaction') or 0)}",
        f"- Missing audit log: {int(summary.get('missing_audit_log') or 0)}",
        "",
        "## Expected Contract",
    ]
    if loaded:
        for r in loaded.get("routes") or []:
            lines.append(f"- {r.get('method')} {r.get('path')} -> {r.get('resource')}.{r.get('action')}")
    else:
        lines.append("- No authority contract provided.")
    lines += ["", "## Inferred Matrix"]
    lines.append("- Inferred matrix generated as review aid; it must be confirmed by the project owner.")
    lines.append(f"- Inferred routes: {len((inferred.get('routes') or {}).keys()) if isinstance(inferred, dict) else 0}")
    lines += ["", "## Diff"]
    for d in diff.get("diffs") or []:
        route = d.get("route") or {}
        lines.append(f"- [{d.get('severity')}/{d.get('status')}] {d.get('rule_id')} {route.get('method')} {route.get('path')}: {d.get('reason')}")
    lines += ["", "## Limitations"]
    for item in diff.get("limitations") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def render_matrix_negative_test_plan(permission_risks, matrix_diff):
    risks = permission_risks.get("risks") if isinstance(permission_risks.get("risks"), list) else []
    diffs = matrix_diff.get("diffs") if isinstance(matrix_diff.get("diffs"), list) else []
    routes = []
    for r in risks:
        route = r.get("route") if isinstance(r.get("route"), dict) else {}
        routes.append((route.get("method"), route.get("path"), r.get("file")))
    for d in diffs:
        route = d.get("route") if isinstance(d.get("route"), dict) else {}
        routes.append((route.get("method"), route.get("path"), ""))
    seen = set()
    lines = ["# AuthZ Negative Test Plan", ""]
    for method, path, file_path in routes:
        key = (method, path)
        if not method and not path:
            continue
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"## {method} {path}")
        lines.append("")
        if file_path:
            lines.append(f"- source: {file_path}")
        lines.append("- anonymous user -> 401")
        lines.append("- authenticated user without permission -> 403")
        lines.append("- wrong role -> 403")
        lines.append("- owner mismatch -> 403")
        lines.append("- tenant mismatch -> 403")
        lines.append("- duplicate sensitive operation -> expected safe failure")
        lines.append("- successful operation should leave expected evidence/audit trail if the contract requires it")
        lines.append("")
    if not seen:
        lines.append("No permission-sensitive routes were selected for negative test suggestions.")
        lines.append("")
    lines.append("These are suggested negative tests, not observed existing tests.")
    lines.append("")
    return "\n".join(lines)

