import os
import shutil
import unittest

from reposense.analysis.authz.authz_export import export_permission_auditor
from reposense.analysis.authz.authz_matrix_export import export_authz_matrix
from tests._tmpdir import make_temp_dir


class AuthZMatrixInferTest(unittest.TestCase):
    def test_without_contract_generates_inferred_only(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "authz_smoke_min"))
        run_dir = make_temp_dir(prefix="authz_matrix_infer_")
        try:
            export_permission_auditor(run_dir, repo_path=repo)
            res = export_authz_matrix(run_dir, repo_path=repo)
            self.assertTrue(os.path.isfile(res["inferred_path"]))
            self.assertEqual((res.get("diff") or {}).get("mode"), "inferred_only")
            self.assertTrue((res.get("inferred") or {}).get("inferred"))
            with open(res["inferred_path"], "r", encoding="utf-8") as f:
                self.assertIn("needs_confirmation", f.read())
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
