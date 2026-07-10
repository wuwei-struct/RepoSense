import os
import shutil
import subprocess
import sys
import unittest

from tests._tmpdir import make_temp_dir


class AuthZMatrixCliTest(unittest.TestCase):
    def test_authz_matrix_cli_writes_outputs(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "authz_matrix_min"))
        run_dir = make_temp_dir(prefix="authz_matrix_cli_")
        try:
            cmd = [sys.executable, "-m", "reposense", "authz", "matrix", run_dir, "--repo", repo, "--contract", os.path.join(repo, "reposense.authz.yaml"), "--json", "--markdown"]
            res = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(res.returncode, 0, res.stderr + res.stdout)
            for name in ["authz_matrix_loaded.json", "authz_matrix_inferred.yaml", "authz_matrix_diff.json", "authz_matrix_report.md", "authz_negative_test_plan.md"]:
                self.assertTrue(os.path.isfile(os.path.join(run_dir, name)), name)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

