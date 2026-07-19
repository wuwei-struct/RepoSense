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
    correlations = tx.get("transaction_correlations") if isinstance(tx.get("transaction_correlations"), dict) else {}
    if correlations:
        coverage = correlations.get("counts_by_coverage_status") or {}
        lines.append(f"- Explicit covered correlations: {int(coverage.get('covered_explicit') or 0)}")
        lines.append(f"- Uncovered correlations: {int(coverage.get('uncovered') or 0)}")
        lines.append(f"- Partial / unknown: {int(coverage.get('partially_covered') or 0)} / {int(coverage.get('unknown') or 0)}")
        lines.append(f"- Read-only transaction writes: {int(coverage.get('read_only_transaction') or 0)}")
    typescript = tx.get("typescript_typeorm_correlations") or {}
    if typescript.get("status") == "enabled":
        mechanisms = typescript.get("counts_by_transaction_mechanism") or {}
        lines.append(
            "- TypeScript callback / QueryRunner / decorator / wrapper correlations: "
            f"{int(mechanisms.get('typeorm_callback') or 0) + int(mechanisms.get('entity_manager_callback') or 0)} / "
            f"{int(mechanisms.get('query_runner') or 0)} / "
            f"{int(mechanisms.get('trusted_decorator_method') or 0) + int(mechanisms.get('trusted_decorator_class') or 0)} / "
            f"{int(mechanisms.get('direct_wrapper_caller') or 0)}"
        )
        lines.append(
            "- TypeScript migration writes requiring policy confirmation: "
            f"{int(typescript.get('migration_unresolved_write_count') or 0)}"
        )
    typeorm = tx.get("typeorm_db_coverage") or {}
    if typeorm.get("status") == "enabled":
        lines.append(
            "- TypeORM DB reads / writes / transactions: "
            f"{int(typeorm.get('db_reads') or 0)} / "
            f"{int(typeorm.get('db_writes') or 0)} / "
            f"{int(typeorm.get('db_transactions') or 0)}"
        )
        lines.append(
            "- TypeORM writes with explicit / unresolved transaction context: "
            f"{int(typeorm.get('writes_with_explicit_transaction_context') or 0)} / "
            f"{int(typeorm.get('writes_with_unresolved_transaction_coverage') or 0)}"
        )
        lines.append(
            f"- TypeORM raw SQL unknown: {int(typeorm.get('raw_sql_unknown') or 0)}"
        )
    lines += ["", "## 5. Queue / Cache Review"]
    counts = (report.get("queue_cache_review") or {}).get("backend_event_counts") or {}
    for k in ["queue.dispatch", "queue.consume", "cache.read", "cache.write", "cache.invalidate"]:
        if k in counts:
            lines.append(f"- {k}: {int(counts.get(k) or 0)}")
    queue_validation = (report.get("queue_cache_review") or {}).get("validation_summary") or {}
    if queue_validation:
        lines.append(
            "- Matched producer/consumer pairs: "
            f"{int(queue_validation.get('matched_producer_consumer_pairs') or 0)}"
        )
        lines.append(
            "- Unmatched dispatches / unresolved names: "
            f"{int(queue_validation.get('unmatched_dispatches') or 0)} / "
            f"{int(queue_validation.get('unknown_name_events') or 0)}"
        )
        lines.append(
            "- Cache operations: "
            f"{int(queue_validation.get('cache_read_count') or 0)} read / "
            f"{int(queue_validation.get('cache_write_count') or 0)} write / "
            f"{int(queue_validation.get('cache_invalidate_count') or 0)} invalidate"
        )
    lines += ["", "## 6. API Surface Review"]
    api = report.get("api_surface_review") or {}
    lines.append(f"- API total: {int(api.get('api_total') or 0)}")
    lines.append(f"- OpenAPI present: {bool(api.get('openapi_present'))}")
    decorators = api.get("route_decorator_classification") or {}
    if decorators.get("status") == "enabled":
        lines.append(
            "- Route decorators accepted / rejected / unknown: "
            f"{int(decorators.get('accepted_route_count') or 0)} / "
            f"{int(decorators.get('rejected_non_route_count') or 0)} / "
            f"{int(decorators.get('unknown_count') or 0)}"
        )
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
        lines.append(f"- Actionable findings: {int(ch.get('actionable_findings') or 0)}")
        lines.append(f"- Excluded from primary review: {int(ch.get('findings_excluded_from_primary_review') or 0)}")
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
        lines.append(f"- Actionable risks: {int(perm.get('actionable_risks') or 0)}")
        lines.append(f"- Public auth entrypoints: {int(perm.get('public_auth_entrypoints') or 0)}")
        lines.append(f"- Routes: {int(perm.get('routes') or 0)}")
        lines.append(f"- Frontend permission signals: {int(perm.get('frontend_permission_signals') or 0)}")
        lines.append(f"- Negative test gaps: {int(perm.get('negative_test_gaps') or 0)}")
        matrix = perm.get("authz_matrix") or {}
        if matrix:
            lines.append(f"- AuthZ Matrix mode: {matrix.get('mode') or 'n/a'}")
            lines.append(f"- Matrix missing auth: {int(matrix.get('missing_auth') or 0)}")
            lines.append(f"- Matrix missing permission: {int(matrix.get('missing_permission') or 0)}")
            lines.append(f"- Matrix missing tenant/transaction/audit: {int(matrix.get('missing_tenant_boundary') or 0)} / {int(matrix.get('missing_transaction') or 0)} / {int(matrix.get('missing_audit_log') or 0)}")
        guards = perm.get("guard_correlation") or {}
        if guards.get("status") == "enabled":
            lines.append(
                "- Guard protected method/controller/global: "
                f"{int(guards.get('protected_method') or 0)} / "
                f"{int(guards.get('protected_controller') or 0)} / "
                f"{int(guards.get('protected_global') or 0)}"
            )
            lines.append(
                "- Intentional public bypasses: "
                f"{int(guards.get('intentional_public_bypasses') or 0)}"
            )
            lines.append(
                "- OpenAPI protected without code guard / OpenAPI-only / unresolved: "
                f"{int(guards.get('openapi_protected_without_code_guard') or 0)} / "
                f"{int(guards.get('openapi_only_routes') or 0)} / "
                f"{int(guards.get('unresolved_routes') or 0)}"
            )
        for k, v in sorted((perm.get("counts_by_rule") or {}).items()):
            lines.append(f"- {k}: {int(v or 0)}")
    else:
        lines.append(f"- Note: {perm.get('note') or 'Permission artifacts were not generated for this run.'}")
    lines += ["", "## 11. Context Calibration"]
    context = report.get("context_calibration") or {}
    lines.append(f"- Status: {context.get('status') or 'not_available'}")
    lines.append(f"- Public auth entrypoints recognized: {int(context.get('public_auth_route_count') or 0)}")
    lines.append(f"- Non-production files classified: {sum(int(context.get(key) or 0) for key in ['generated_file_count', 'seed_file_count', 'template_file_count', 'fixture_file_count'])}")
    lines.append(f"- Findings downweighted: {int(context.get('findings_downweighted_count') or 0)}")
    lines.append(f"- Findings excluded from primary review: {int(context.get('findings_excluded_from_primary_review_count') or 0)}")
    lines.append(f"- Unresolved route intent conflicts: {int(context.get('route_intent_conflict_count') or 0)}")
    lines += ["", "## 12. Human Review Required"]
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
    lines += ["## 13. Limitations"]
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
