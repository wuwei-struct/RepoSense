import os
import shutil
import unittest

from reposense.analysis.authz.authz_export import export_permission_auditor
from reposense.analysis.authz.authz_matrix_export import export_authz_matrix
from tests._tmpdir import make_temp_dir


class AuthZMatrixDiffTest(unittest.TestCase):
    def test_contract_diff_detects_expected_missing_signals(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "authz_matrix_min"))
        run_dir = make_temp_dir(prefix="authz_matrix_diff_")
        try:
            export_permission_auditor(run_dir, repo_path=repo)
            res = export_authz_matrix(run_dir, repo_path=repo, contract_path=os.path.join(repo, "reposense.authz.yaml"))
            diff = res.get("diff") or {}
            self.assertEqual(diff.get("mode"), "contract_diff")
            rules = {d.get("rule_id") for d in diff.get("diffs") or []}
            self.assertNotIn("AUTHZ-MATRIX-001", rules)
            self.assertIn("AUTHZ-MATRIX-002", rules)
            self.assertIn("AUTHZ-MATRIX-004", rules)
            self.assertIn("AUTHZ-MATRIX-005", rules)
            self.assertIn("AUTHZ-MATRIX-006", rules)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

