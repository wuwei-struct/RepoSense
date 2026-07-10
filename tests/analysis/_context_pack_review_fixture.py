import json
import os

from tests._tmpdir import make_temp_dir


def build_review_context_run():
    run_dir = make_temp_dir(prefix="ctx_review_run_")
    files = {
        "report.json": {"run_summary": {"findings_count": 0, "events_count": 0}, "findings": []},
        "event_graph.json": {"nodes": [], "edges": []},
        "coverage.json": {"walk": {"included_files": 1}, "warnings": []},
        "backend_verifier_report.md": "# Backend Verifier Report\n",
        "repository_review_report.md": "# Repository Review Report\n",
        "review_risk_matrix.json": {"decision": "WARN", "human_review_required_count": 2},
        "human_review_required.md": "# Human Review Required\n\n## src/service.ts\n",
        "code_health_summary.json": {"total_findings": 3, "health_score": {"score": 82}},
        "maintainability_risks.json": {"risks": [{"file": "src/service.ts", "reason": "giant file found"}]},
        "permission_risk_report.md": "# Permission Risk Report\n",
        "permission_risks.json": {"risks": [{"file": "src/server.ts", "reason": "Write-like endpoint observed without auth guard evidence.", "severity": "medium"}]},
        "human_permission_review_required.md": "# Human Permission Review Required\n",
        "authz_matrix_report.md": "# AuthZ Matrix Report\n",
        "authz_matrix_diff.json": {"mode": "contract_diff", "summary": {"missing_auth": 1, "missing_permission": 1}, "diffs": [{"route": {"method": "POST", "path": "/api/orders"}, "reason": "Expected permission signal not observed."}]},
        "authz_negative_test_plan.md": "# AuthZ Negative Test Plan\n",
    }
    for rel, content in files.items():
        path = os.path.join(run_dir, rel)
        os.makedirs(os.path.dirname(path) or run_dir, exist_ok=True)
        if isinstance(content, dict):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(content, f)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
    return run_dir

