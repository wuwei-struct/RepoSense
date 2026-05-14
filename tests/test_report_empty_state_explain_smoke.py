import os
import json
import tempfile
import unittest
from reposense.scan import run_scan


class ReportEmptyStateExplainSmokeTest(unittest.TestCase):
    def test_empty_state_explain_present(self):
        # create repo with only binary to force zero findings/events and skipped
        repo = tempfile.mkdtemp(prefix="repo_empty_")
        with open(os.path.join(repo, "bin.dat"), "wb") as f:
            f.write(b"\x00" * 1024)
        out = tempfile.mkdtemp(prefix="out_empty_")
        rd = run_scan(repo, out, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2")), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json")))
        with open(os.path.join(rd, "report.html"), "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("空状态解释", html)


if __name__ == "__main__":
    unittest.main()

