import json
import os
import shutil
import unittest

from reposense.analysis.authz.authz_export import export_permission_auditor
from reposense.analysis.authz.authz_matrix_export import export_authz_matrix
from reposense.analysis.review.review_export import export_repository_review_report
from tests._tmpdir import make_temp_dir


class AuthZMatrixIntegrationTest(unittest.TestCase):
    def test_matrix_then_repository_review(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "authz_matrix_min"))
        run_dir = make_temp_dir(prefix="authz_matrix_int_")
        try:
            export_permission_auditor(run_dir, repo_path=repo)
            export_authz_matrix(run_dir, repo_path=repo, contract_path=os.path.join(repo, "reposense.authz.yaml"))
            review = export_repository_review_report(run_dir)
            with open(review["report_json_path"], "r", encoding="utf-8") as f:
                obj = json.load(f)
            matrix = ((obj.get("permission_review") or {}).get("authz_matrix") or {})
            self.assertEqual(matrix.get("mode"), "contract_diff")
            self.assertGreater(matrix.get("missing_permission") or 0, 0)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

