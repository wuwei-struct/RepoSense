import importlib.util
import json
import os
import shutil
import unittest

from tests._tmpdir import make_temp_dir


def _load_module():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    path = os.path.join(root, "tools", "validation", "real_repo_smoke.py")
    spec = importlib.util.spec_from_file_location("real_repo_smoke_local", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_queue_cache_module():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    path = os.path.join(root, "tools", "validation", "queue_cache_validation.py")
    spec = importlib.util.spec_from_file_location("queue_cache_validation_local", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RealRepoSmokeLocalFixtureTest(unittest.TestCase):
    def test_local_fixture_can_be_validated_without_network_or_execution(self):
        module = _load_module()
        queue_cache_module = _load_queue_cache_module()
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        repo = os.path.join(root, "tests", "fixtures", "repos", "review_demo_full")
        script_path = os.path.join(root, "tools", "real_repo_review_smoke.ps1")
        self.assertTrue(os.path.isdir(repo))
        with open(script_path, "r", encoding="utf-8") as handle:
            script = handle.read()
        self.assertIn("[string]$RepoPath", script)
        self.assertIn("[switch]$AllowNetwork", script)
        self.assertIn("target_code_executed = $false", script)
        for forbidden in ["npm install", "npm test", "mvn test", "gradle test", "yarn install", "pnpm install"]:
            self.assertNotIn(forbidden, script.lower())

        temp = make_temp_dir(prefix="real_repo_local_fixture_")
        try:
            run = os.path.join(temp, "run")
            os.makedirs(run)
            source_file = "src/services/riskyService.ts"
            json_artifacts = {
                "report.json": {
                    "findings": [
                        {
                            "fid": 1,
                            "rule_id": "fixture",
                            "path": source_file,
                            "start_line": 1,
                            "snippet": "export function rebuildAdminState(input: any) {",
                        }
                    ]
                },
                "backend_verifier_report.json": {},
                "patterns.json": {"patterns": []},
                "code_health.json": {"findings": []},
                "permission_surface.json": {"routes": []},
                "permission_risks.json": {"risks": []},
                "authz_matrix_diff.json": {"mode": "inferred_only", "summary": {}, "diffs": []},
                "repository_review_report.json": {"human_review_required": []},
                "review_risk_matrix.json": {"decision": "PASS", "human_review_required_count": 0},
                "coverage.json": {"walk": {"included_files": 1}, "warnings": []},
                "event_graph.json": {"nodes": [], "edges": []},
                "api_surface.json": {"endpoints": []},
                "transaction_correlations.json": {"correlations": []},
                "transaction_correlation_summary.json": {
                    "total_correlations": 0
                },
                "route_intent_annotations.json": {"annotations": []},
                "file_context_annotations.json": {"annotations": []},
                "review_context_summary.json": {},
                "route_guard_correlations.json": {"correlations": []},
                "route_guard_summary.json": {},
                "openapi_security_surface.json": {
                    "specs": [],
                    "routes": [],
                },
                "route_decorator_classifications.json": {
                    "classifications": []
                },
                "route_decorator_summary.json": {
                    "candidate_count": 0,
                    "accepted_route_count": 0,
                    "rejected_non_route_count": 0,
                    "unknown_count": 0,
                },
                "run_manifest.json": {"artifacts": []},
            }
            for rel, payload in json_artifacts.items():
                with open(os.path.join(run, rel), "w", encoding="utf-8") as handle:
                    json.dump(payload, handle)
            text_artifacts = [
                "report.html",
                "backend_verifier_report.md",
                "repository_review_report.md",
                "human_review_required.md",
                "context_pack/REVIEW/README.md",
            ]
            for rel in text_artifacts:
                path = os.path.join(run, rel)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write("fixture\n")
            with open(os.path.join(run, "authz_matrix_inferred.yaml"), "w", encoding="utf-8") as handle:
                handle.write("inferred: true\nroutes: {}\n")
            queue_cache_module.write_validation(
                run,
                repo,
                case_id="local-review-demo",
            )
            validation = module.build_case_validation(
                "local-review-demo",
                run,
                repo,
                {"source_mode": "local_path", "target_code_executed": False},
                {"completed": True, "stages": [{"stage": "verify_strict", "ok": True, "exit_code": 0}]},
            )
            self.assertTrue(validation["artifact_completeness"]["complete"])
            self.assertTrue(validation["evidence_integrity"]["passed"])
            self.assertTrue(validation["strict_verification"]["passed"])
            self.assertTrue(validation["ready_for_manual_calibration"])
        finally:
            shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
