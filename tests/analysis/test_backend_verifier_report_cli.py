import os
import shutil
import subprocess
import sys
import unittest

from tests.analysis._ai_summary_fixture import build_ai_summary_run_dir


class BackendVerifierReportCliTest(unittest.TestCase):
    def test_cli_backend_report(self):
        rd = build_ai_summary_run_dir()
        try:
            cmd = [sys.executable, "-m", "reposense", "backend", "report", rd, "--json", "--markdown"]
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(p.returncode, 0)
            self.assertTrue(os.path.isfile(os.path.join(rd, "backend_verifier_report.json")))
            self.assertTrue(os.path.isfile(os.path.join(rd, "backend_verifier_report.md")))
        finally:
            shutil.rmtree(rd, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

