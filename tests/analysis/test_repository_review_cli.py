import os
import shutil
import subprocess
import sys
import unittest

from reposense.analysis.ai.pattern_export import export_patterns
from reposense.analysis.ai.risks_export import export_ai_risks
from reposense.analysis.reports.backend_verifier_report import export_backend_verifier_report
from tests.analysis._ai_summary_fixture import build_ai_summary_run_dir


class RepositoryReviewCliTest(unittest.TestCase):
    def test_cli_review_report(self):
        rd = build_ai_summary_run_dir()
        try:
            export_backend_verifier_report(rd)
            export_patterns(rd)
            export_ai_risks(rd, no_drilldown=True)
            cmd = [sys.executable, "-m", "reposense", "review", "report", rd, "--json", "--markdown"]
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(p.returncode, 0, p.stderr.decode("utf-8", errors="replace"))
            self.assertTrue(os.path.isfile(os.path.join(rd, "repository_review_report.json")))
            self.assertTrue(os.path.isfile(os.path.join(rd, "repository_review_report.md")))
            self.assertTrue(os.path.isfile(os.path.join(rd, "review_risk_matrix.json")))
            self.assertTrue(os.path.isfile(os.path.join(rd, "human_review_required.md")))
        finally:
            shutil.rmtree(rd, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

