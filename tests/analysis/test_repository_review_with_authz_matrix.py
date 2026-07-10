import json
import os
import shutil
import unittest

from reposense.analysis.authz.authz_matrix_export import export_authz_matrix
from reposense.analysis.review.review_export import export_repository_review_report
from tests.analysis._ai_summary_fixture import build_ai_summary_run_dir


class RepositoryReviewWithAuthZMatrixTest(unittest.TestCase):
    def test_review_consumes_authz_matrix_diff(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "authz_matrix_min"))
        run_dir = build_ai_summary_run_dir()
        try:
            export_authz_matrix(run_dir, repo_path=repo, contract_path=os.path.join(repo, "reposense.authz.yaml"))
            res = export_repository_review_report(run_dir)
            with open(res["report_json_path"], "r", encoding="utf-8") as f:
                report = json.load(f)
            matrix = (report.get("permission_review") or {}).get("authz_matrix") or {}
            self.assertEqual(matrix.get("mode"), "contract_diff")
            with open(res["human_review_path"], "r", encoding="utf-8") as f:
                self.assertIn("Expected permission signal not observed", f.read())
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

