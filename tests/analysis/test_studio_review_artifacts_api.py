import json
import os
import tempfile
import unittest

from reposense.studio.server import build_review_metadata


class StudioReviewArtifactsApiTest(unittest.TestCase):
    def test_review_metadata_empty_when_artifacts_missing(self):
        with tempfile.TemporaryDirectory() as td:
            meta = build_review_metadata("run-empty", td)
            self.assertFalse(meta["available"])
            self.assertEqual(meta["artifacts"], {})

    def test_review_metadata_includes_existing_artifacts_and_summary(self):
        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "context_pack", "REVIEW"), exist_ok=True)
            files = {
                "repository_review_report.md": "# Repository Review\n",
                "human_review_required.md": "# Human Review Required\n",
                "code_health_summary.json": json.dumps({"total_findings": 2, "counts_by_severity": {"medium": 2}}),
                "permission_risk_report.md": "# Permission Risk Report\n",
                "permission_risks.json": json.dumps({"risks": [{"severity": "high"}, {"severity": "medium"}]}),
                "authz_matrix_report.md": "# AuthZ Matrix Report\n",
                "authz_matrix_diff.json": json.dumps({"mode": "contract_diff", "summary": {"missing_auth": 1}}),
                "authz_negative_test_plan.md": "# AuthZ Negative Test Plan\n",
                os.path.join("context_pack", "REVIEW", "README.md"): "# Repository Review Context\n",
                os.path.join("context_pack", "REVIEW", "ai_maintenance_constraints.md"): "# AI Maintenance Constraints\n",
                "review_risk_matrix.json": json.dumps({
                    "decision": "WARN",
                    "counts": {"high": 1, "medium": 2, "low": 0},
                    "human_review_required_count": 3,
                    "top_risks": [{"title": "Check auth"}],
                }),
            }
            for rel, content in files.items():
                path = os.path.join(td, rel)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)

            meta = build_review_metadata("run-123", td)
            self.assertTrue(meta["available"])
            self.assertEqual(meta["decision"], "WARN")
            self.assertEqual(meta["human_review_required_count"], 3)
            self.assertIn("human_review_required", meta["artifacts"])
            self.assertIn("review_context", meta["artifacts"])
            self.assertIn("/runs/run-123/human_review_required.md", meta["artifacts"]["human_review_required"]["url"])
            self.assertEqual(meta["code_health"]["total_findings"], 2)
            self.assertEqual(meta["permission"]["total_risks"], 2)
            self.assertEqual(meta["authz_matrix"]["mode"], "contract_diff")


if __name__ == "__main__":
    unittest.main()
