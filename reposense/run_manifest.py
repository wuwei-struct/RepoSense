import os
import json
import hashlib
import glob
def _sha256(path):
    try:
        with open(path, "rb") as f:
            h = hashlib.sha256()
            while True:
                b = f.read(8192)
                if not b: break
                h.update(b)
            return h.hexdigest()
    except Exception:
        return None
def _artifact_kind(rel):
    if rel == "report.json": return "report"
    if rel == "event_graph.json": return "event_graph"
    if rel == "api_surface.json": return "api_surface"
    if rel == "entrypoints.json": return "entrypoints"
    if rel == "coverage.json": return "coverage"
    if rel == "ci_summary.json": return "ci_summary"
    if rel == "quality_gate.json": return "quality_gate"
    if rel == "patterns.json": return "patterns"
    if rel == "pattern_summary.json": return "pattern_summary"
    if rel == "transaction_correlations.json": return "transaction_correlation"
    if rel == "transaction_correlation_summary.json": return "transaction_correlation"
    if rel == "route_intent_annotations.json": return "review_context"
    if rel == "file_context_annotations.json": return "review_context"
    if rel == "review_context_summary.json": return "review_context"
    if rel == "route_guard_correlations.json": return "route_guard_correlation"
    if rel == "route_guard_summary.json": return "route_guard_correlation"
    if rel == "openapi_security_surface.json": return "route_guard_correlation"
    if rel == "route_decorator_classifications.json": return "route_decorator_classification"
    if rel == "route_decorator_summary.json": return "route_decorator_classification"
    if rel == "queue_cache_validation.json": return "queue_cache_validation"
    if rel == "queue_cache_validation.md": return "queue_cache_validation"
    if rel.startswith("queue_reliability_"): return "queue_reliability"
    if rel.startswith("queue_retry_idempotency_validation"): return "queue_reliability"
    if rel == "typeorm_db_operations.json": return "typeorm_db_operation"
    if rel == "typeorm_db_summary.json": return "typeorm_db_operation"
    if rel == "typeorm_db_validation.json": return "typeorm_db_validation"
    if rel == "typeorm_db_validation.md": return "typeorm_db_validation"
    if rel == "typescript_transaction_validation.json": return "typescript_transaction_validation"
    if rel == "typescript_transaction_validation.md": return "typescript_transaction_validation"
    if rel in {"typescript_import_graph.json", "typescript_symbol_index.json"}: return "typescript_symbol_resolution"
    if rel.startswith("typeorm_alias_"): return "typeorm_alias_resolution"
    if rel == "ai_summary.json": return "ai_summary"
    if rel == "ai_summary.md": return "ai_summary"
    if rel.endswith("/snippet_pack.json") and rel.startswith("ai_drilldown/"): return "ai_drilldown"
    if rel.endswith("/snippet_pack.md") and rel.startswith("ai_drilldown/"): return "ai_drilldown"
    if rel.endswith("/explain.json") and rel.startswith("ai_explain/"): return "ai_explain"
    if rel.endswith("/explain.md") and rel.startswith("ai_explain/"): return "ai_explain"
    if rel == "ai_risks/risks.json": return "ai_risks"
    if rel == "ai_risks/risks.md": return "ai_risks"
    if rel == "backend_verifier_report.json": return "backend_verifier_report"
    if rel == "backend_verifier_report.md": return "backend_verifier_report"
    if rel == "repository_review_report.json": return "repository_review"
    if rel == "repository_review_report.md": return "repository_review"
    if rel == "review_risk_matrix.json": return "repository_review"
    if rel == "human_review_required.md": return "repository_review"
    if rel == "code_health.json": return "code_health"
    if rel == "code_health_summary.json": return "code_health"
    if rel == "maintainability_risks.json": return "code_health"
    if rel == "permission_surface.json": return "permission_auditor"
    if rel == "permission_risks.json": return "permission_auditor"
    if rel == "permission_risk_report.md": return "permission_auditor"
    if rel == "human_permission_review_required.md": return "permission_auditor"
    if rel == "authz_negative_test_plan.md": return "authz_matrix"
    if rel == "authz_matrix_loaded.json": return "authz_matrix"
    if rel == "authz_matrix_inferred.yaml": return "authz_matrix"
    if rel == "authz_matrix_diff.json": return "authz_matrix"
    if rel == "authz_matrix_report.md": return "authz_matrix"
    if rel.endswith("/answer.json") and rel.startswith("ai_ask/"): return "ai_ask"
    if rel.endswith("/answer.md") and rel.startswith("ai_ask/"): return "ai_ask"
    if rel.startswith("exports/"): return "exports"
    if rel.startswith("context_pack/"): return "context_pack"
    return "other"
def build_run_manifest(run_dir, write=True):
    artifacts = []
    rels = ["report.json","event_graph.json","api_surface.json","entrypoints.json","coverage.json","ci_summary.json","quality_gate.json","api_callers.json","cross_language_links.json","cross_language_summary.json","api_topology.json","patterns.json","pattern_summary.json","transaction_correlations.json","transaction_correlation_summary.json","route_intent_annotations.json","file_context_annotations.json","review_context_summary.json","ai_summary.json","ai_summary.md","ai_risks/risks.json","ai_risks/risks.md","backend_verifier_report.json","backend_verifier_report.md","repository_review_report.json","repository_review_report.md","review_risk_matrix.json","human_review_required.md","code_health.json","code_health_summary.json","maintainability_risks.json","permission_surface.json","permission_risks.json","permission_risk_report.md","human_permission_review_required.md","authz_negative_test_plan.md","authz_matrix_loaded.json","authz_matrix_inferred.yaml","authz_matrix_diff.json","authz_matrix_report.md","baseline_in.json","baseline_diff.json","baseline_diff.md","exports/report.sarif.json","context_pack/ARTIFACTS/run_summary.json","context_pack/ARTIFACTS/quality_gate.json","context_pack/ARTIFACTS/baseline_diff.json","context_pack/ARTIFACTS/baseline_in.json","context_pack/ARTIFACTS/run_manifest.json","context_pack/ARTIFACTS/api_callers.json","context_pack/ARTIFACTS/cross_language_summary.json","context_pack/ARTIFACTS/patterns.json","context_pack/ARTIFACTS/pattern_summary.json","context_pack/ARTIFACTS/transaction_correlations.json","context_pack/ARTIFACTS/transaction_correlation_summary.json","context_pack/ARTIFACTS/route_intent_annotations.json","context_pack/ARTIFACTS/file_context_annotations.json","context_pack/ARTIFACTS/review_context_summary.json","context_pack/ARTIFACTS/ai_summary.json","context_pack/ARTIFACTS/ai_summary.md","context_pack/ARTIFACTS/code_health.json","context_pack/ARTIFACTS/code_health_summary.json","context_pack/ARTIFACTS/maintainability_risks.json","context_pack/ARTIFACTS/permission_surface.json","context_pack/ARTIFACTS/permission_risks.json","context_pack/ARTIFACTS/permission_risk_report.md","context_pack/ARTIFACTS/human_permission_review_required.md","context_pack/ARTIFACTS/authz_negative_test_plan.md","context_pack/ARTIFACTS/authz_matrix_loaded.json","context_pack/ARTIFACTS/authz_matrix_inferred.yaml","context_pack/ARTIFACTS/authz_matrix_diff.json","context_pack/ARTIFACTS/authz_matrix_report.md","context_pack/MAP/cross_language_links.json","context_pack/MAP/api_topology.json"]
    rels.extend([
        "route_guard_correlations.json",
        "route_guard_summary.json",
        "openapi_security_surface.json",
        "context_pack/ARTIFACTS/route_guard_correlations.json",
        "context_pack/ARTIFACTS/route_guard_summary.json",
        "context_pack/ARTIFACTS/openapi_security_surface.json",
        "route_decorator_classifications.json",
        "route_decorator_summary.json",
        "context_pack/ARTIFACTS/route_decorator_classifications.json",
        "context_pack/ARTIFACTS/route_decorator_summary.json",
        "queue_cache_validation.json",
        "queue_cache_validation.md",
        "queue_reliability_correlations.json",
        "queue_reliability_summary.json",
        "queue_reliability_risks.json",
        "queue_retry_idempotency_validation.json",
        "queue_retry_idempotency_validation.md",
        "context_pack/ARTIFACTS/queue_cache_validation.json",
        "context_pack/ARTIFACTS/queue_cache_validation.md",
        "context_pack/ARTIFACTS/queue_reliability_correlations.json",
        "context_pack/ARTIFACTS/queue_reliability_summary.json",
        "context_pack/ARTIFACTS/queue_reliability_risks.json",
        "context_pack/ARTIFACTS/queue_retry_idempotency_validation.json",
        "context_pack/ARTIFACTS/queue_retry_idempotency_validation.md",
        "typeorm_db_operations.json",
        "typeorm_db_summary.json",
        "typeorm_db_validation.json",
        "typeorm_db_validation.md",
        "context_pack/ARTIFACTS/typeorm_db_operations.json",
        "context_pack/ARTIFACTS/typeorm_db_summary.json",
        "context_pack/ARTIFACTS/typeorm_db_validation.json",
        "context_pack/ARTIFACTS/typeorm_db_validation.md",
        "typescript_transaction_validation.json",
        "typescript_transaction_validation.md",
        "context_pack/ARTIFACTS/typescript_transaction_validation.json",
        "context_pack/ARTIFACTS/typescript_transaction_validation.md",
        "typescript_import_graph.json",
        "typescript_symbol_index.json",
        "typeorm_alias_resolutions.json",
        "typeorm_alias_resolution_summary.json",
        "typeorm_alias_validation.json",
        "typeorm_alias_validation.md",
        "context_pack/ARTIFACTS/typescript_import_graph.json",
        "context_pack/ARTIFACTS/typescript_symbol_index.json",
        "context_pack/ARTIFACTS/typeorm_alias_resolutions.json",
        "context_pack/ARTIFACTS/typeorm_alias_resolution_summary.json",
        "context_pack/ARTIFACTS/typeorm_alias_validation.json",
        "context_pack/ARTIFACTS/typeorm_alias_validation.md",
    ])
    for p in sorted(glob.glob(os.path.join(run_dir, "ai_drilldown", "*", "snippet_pack.json"))):
        rels.append(os.path.relpath(p, run_dir).replace("\\", "/"))
    for p in sorted(glob.glob(os.path.join(run_dir, "ai_drilldown", "*", "snippet_pack.md"))):
        rels.append(os.path.relpath(p, run_dir).replace("\\", "/"))
    for p in sorted(glob.glob(os.path.join(run_dir, "ai_explain", "*", "explain.json"))):
        rels.append(os.path.relpath(p, run_dir).replace("\\", "/"))
    for p in sorted(glob.glob(os.path.join(run_dir, "ai_explain", "*", "explain.md"))):
        rels.append(os.path.relpath(p, run_dir).replace("\\", "/"))
    for p in sorted(glob.glob(os.path.join(run_dir, "ai_ask", "*", "answer.json"))):
        rels.append(os.path.relpath(p, run_dir).replace("\\", "/"))
    for p in sorted(glob.glob(os.path.join(run_dir, "ai_ask", "*", "answer.md"))):
        rels.append(os.path.relpath(p, run_dir).replace("\\", "/"))
    for rel in rels:
        p = os.path.join(run_dir, rel)
        if os.path.isfile(p):
            sha = _sha256(p)
            artifacts.append({
                "path": rel,
                "kind": _artifact_kind(rel),
                "schema_version": None,
                "bytes": os.path.getsize(p),
                "sha256": sha,
                "generated_by": None
            })
    # stable sorting
    artifacts.sort(key=lambda x: (x["kind"], x["path"]))
    meta = {"run_dir": run_dir}
    try:
        with open(os.path.join(run_dir, "coverage.json"), "r", encoding="utf-8") as f:
            cov = json.load(f)
        meta["content_id"] = cov.get("content_id")
        meta["pack_id"] = cov.get("pack_id")
    except Exception:
        pass
    try:
        with open(os.path.join(run_dir, "report.json"), "r", encoding="utf-8") as f:
            rep = json.load(f)
        rsid = ((rep.get("generated_by") or {}).get("ruleset_id")) or None
        rsfp = ((rep.get("generated_by") or {}).get("ruleset_fingerprint")) or None
        meta["profile"] = (rep.get("run_summary") or {}).get("profile")
        meta["ruleset_id"] = rsid
        meta["ruleset_fingerprint"] = rsfp
    except Exception:
        pass
    gb = None
    try:
        with open(os.path.join(run_dir, "quality_gate.json"), "r", encoding="utf-8") as f:
            gb = json.load(f).get("generated_by")
    except Exception:
        try:
            with open(os.path.join(run_dir, "report.json"), "r", encoding="utf-8") as f:
                gb = json.load(f).get("generated_by")
        except Exception:
            gb = None
    out = {"schema_version": 1, "meta": meta, "artifacts": artifacts, "generated_by": gb}
    if write:
        with open(os.path.join(run_dir, "run_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False)
    return out
