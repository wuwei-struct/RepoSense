import os
import shutil
import subprocess
import sys
import unittest

from tests._tmpdir import make_temp_dir


class PermissionAuditorCliTest(unittest.TestCase):
    def test_authz_scan_cli_writes_outputs(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "authz_smoke_min"))
        run_dir = make_temp_dir(prefix="authz_cli_run_")
        try:
            cmd = [sys.executable, "-m", "reposense", "authz", "scan", run_dir, "--repo", repo, "--json", "--markdown"]
            res = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(res.returncode, 0, res.stderr + res.stdout)
            for name in ["permission_surface.json", "permission_risks.json", "permission_risk_report.md", "human_permission_review_required.md", "authz_negative_test_plan.md"]:
                self.assertTrue(os.path.isfile(os.path.join(run_dir, name)), name)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

