def render_repository_review_markdown(report):
    summary = report.get("review_summary") or {}
    matrix = report.get("risk_matrix") or {}
    lines = [
        "# RepoSense Repository Review Report",
        "",
        "## 1. Review Summary",
        f"- Decision: {summary.get('decision') or matrix.get('decision') or 'PASS'}",
        f"- Total risks: {int(summary.get('total_risks') or 0)}",
        f"- Human review required: {int(summary.get('human_review_required_count') or 0)}",
        f"- Quality gate: {summary.get('gate_status') or 'n/a'}",
        "",
        "## 2. Backend Risk Review",
    ]
    for r in (report.get("backend_risk_review") or {}).get("top_risks") or []:
        lines.append(f"- [{r.get('severity')}] {r.get('title')} ({r.get('status')})")
    lines += ["", "## 3. Side-effect Review"]
    for row in ((report.get("side_effect_review") or {}).get("paths") or [])[:10]:
        lines.append(f"- {row.get('path')}: complexity={int(row.get('write_path_complexity') or 0)}")
    lines += ["", "## 4. Transaction Review"]
    tx = report.get("transaction_review") or {}
    lines.append(f"- Transaction signal count: {int(tx.get('transaction_signal_count') or 0)}")
    lines.append(f"- Transaction-related patterns: {len(tx.get('transaction_related_patterns') or [])}")
    lines += ["", "## 5. Queue / Cache Review"]
    counts = (report.get("queue_cache_review") or {}).get("backend_event_counts") or {}
    for k in ["queue.dispatch", "queue.consume", "cache.read", "cache.write", "cache.invalidate"]:
        if k in counts:
            lines.append(f"- {k}: {int(counts.get(k) or 0)}")
    lines += ["", "## 6. API Surface Review"]
    api = report.get("api_surface_review") or {}
    lines.append(f"- API total: {int(api.get('api_total') or 0)}")
    lines.append(f"- OpenAPI present: {bool(api.get('openapi_present'))}")
    lines += ["", "## 7. Pattern Risk Review"]
    pr = report.get("pattern_risk_review") or {}
    lines.append(f"- Total patterns: {int(pr.get('total_patterns') or 0)}")
    for k, v in sorted((pr.get("counts_by_type") or {}).items()):
        lines.append(f"- {k}: {int(v or 0)}")
    lines += ["", "## 8. Quality Gate Review"]
    qg = report.get("quality_gate_review") or {}
    lines.append(f"- Status: {qg.get('status') or 'n/a'}")
    lines.append(f"- Violations: {len(qg.get('violations') or [])}")
    lines += ["", "## 9. Code Health Review"]
    ch = report.get("code_health_review") or {}
    lines.append(f"- Status: {ch.get('status') or 'not_available'}")
    if ch.get("status") == "enabled":
        lines.append(f"- Total findings: {int(ch.get('total_findings') or 0)}")
        hs = ch.get("health_score") or {}
        if hs:
            lines.append(f"- Health score: {int(hs.get('score') or 0)} ({hs.get('note') or 'experimental'})")
        for k, v in sorted((ch.get("counts_by_rule") or {}).items()):
            lines.append(f"- {k}: {int(v or 0)}")
    else:
        lines.append(f"- Note: {ch.get('note') or 'Code Health artifacts were not generated for this run.'}")
    lines += ["", "## 10. Permission Review"]
    perm = report.get("permission_review") or {}
    lines.append(f"- Status: {perm.get('status') or 'not_available'}")
    if perm.get("status") == "enabled":
        lines.append(f"- Total risks: {int(perm.get('total_risks') or 0)}")
        lines.append(f"- Routes: {int(perm.get('routes') or 0)}")
        lines.append(f"- Frontend permission signals: {int(perm.get('frontend_permission_signals') or 0)}")
        lines.append(f"- Negative test gaps: {int(perm.get('negative_test_gaps') or 0)}")
        matrix = perm.get("authz_matrix") or {}
        if matrix:
            lines.append(f"- AuthZ Matrix mode: {matrix.get('mode') or 'n/a'}")
            lines.append(f"- Matrix missing auth: {int(matrix.get('missing_auth') or 0)}")
            lines.append(f"- Matrix missing permission: {int(matrix.get('missing_permission') or 0)}")
            lines.append(f"- Matrix missing tenant/transaction/audit: {int(matrix.get('missing_tenant_boundary') or 0)} / {int(matrix.get('missing_transaction') or 0)} / {int(matrix.get('missing_audit_log') or 0)}")
        for k, v in sorted((perm.get("counts_by_rule") or {}).items()):
            lines.append(f"- {k}: {int(v or 0)}")
    else:
        lines.append(f"- Note: {perm.get('note') or 'Permission artifacts were not generated for this run.'}")
    lines += ["", "## 11. Human Review Required"]
    for idx, item in enumerate(report.get("human_review_required") or [], 1):
        lines.append(f"### {idx}. {item.get('path') or '(artifact evidence)'}")
        lines.append("")
        lines.append("Reason:")
        for r in item.get("reason") or []:
            lines.append(f"- {r}")
        lines.append("")
        lines.append("Suggested reviewer:")
        lines.append(f"- {item.get('suggested_reviewer') or 'backend owner'}")
        lines.append("")
        lines.append("Required decision:")
        for q in item.get("required_decision") or []:
            lines.append(f"- {q}")
        lines.append("")
    lines += ["## 12. Limitations"]
    for item in report.get("limitations") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def render_human_review_required_markdown(items):
    lines = ["# Human Review Required", ""]
    if not items:
        lines += [
            "No evidence-linked human review items were generated from current patterns/risks.",
            "",
        ]
        return "\n".join(lines)
    for idx, item in enumerate(items, 1):
        lines.append(f"## {idx}. {item.get('path') or '(artifact evidence)'}")
        lines.append("")
        lines.append("Reason:")
        for r in item.get("reason") or []:
            lines.append(f"- {r}")
        lines.append("")
        lines.append("Suggested reviewer:")
        lines.append(f"- {item.get('suggested_reviewer') or 'backend owner'}")
        lines.append("")
        lines.append("Required decision:")
        for q in item.get("required_decision") or []:
            lines.append(f"- {q}")
        lines.append("")
    return "\n".join(lines)
