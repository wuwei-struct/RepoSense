import os
import tempfile
import unittest
from reposense.scan import run_scan


class ReportStartHerePresentTest(unittest.TestCase):
    def test_report_contains_start_here(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "entrypoints_min"))
        out = tempfile.mkdtemp(prefix="entry_report_run_")
        rd = run_scan(repo, out, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2")), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json")))
        with open(os.path.join(rd, "report.html"), "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("Start Here", html)


if __name__ == "__main__":
    unittest.main()

