import json
import os
import tempfile
import unittest

from reposense.studio.server import build_run_artifact_metadata


def _write_json(root, relative_path, value):
    path = os.path.join(root, relative_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle)


class StudioRunSummaryApiTest(unittest.TestCase):
    def test_metadata_returns_available_artifacts_and_summary(self):
        with tempfile.TemporaryDirectory() as td:
            _write_json(td, "review_risk_matrix.json", {"decision": "REVIEW", "human_review_required_count": 3})
            _write_json(td, "code_health_summary.json", {"total_findings": 2})
            _write_json(td, "permission_risks.json", {"risks": [{}, {}]})
            _write_json(td, "typeorm_db_summary.json", {"total_operations": 4})
            _write_json(td, "transaction_correlation_summary.json", {"total_correlations": 5})
            _write_json(td, "queue_reliability_summary.json", {"actionable_suspected_risks": 1})
            _write_json(td, "pattern_summary.json", {"total_patterns": 6})
            for relative_path in ["repository_review_report.md", "report.html"]:
                with open(os.path.join(td, relative_path), "w", encoding="utf-8") as handle:
                    handle.write("artifact")

            metadata = build_run_artifact_metadata("run id", td)

            self.assertEqual(metadata["summary"]["review_decision"], "REVIEW")
            self.assertEqual(metadata["summary"]["human_review_required_count"], 3)
            self.assertEqual(metadata["summary"]["counts"]["patterns"], 6)
            self.assertEqual(metadata["summary"]["counts"]["permission_risks"], 2)
            self.assertEqual(metadata["summary"]["count_availability"]["typeorm_operations"], "available")
            artifacts = [item for group in metadata["artifact_groups"] for item in group["artifacts"]]
            report = next(item for item in artifacts if item["artifact_id"] == "repository_review_report")
            self.assertEqual(report["url"], "/runs/run%20id/repository_review_report.md")
            self.assertNotIn("url", metadata["missing_capabilities"][0])

    def test_malformed_summary_is_warning_not_api_failure(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "code_health_summary.json"), "w", encoding="utf-8") as handle:
                handle.write("{not json")
            metadata = build_run_artifact_metadata("run-bad", td)
            self.assertIn("code_health_summary.json could not be parsed", metadata["summary"]["warnings"])
            self.assertEqual(metadata["summary"]["count_availability"]["code_health"], "not_available")


if __name__ == "__main__":
    unittest.main()
