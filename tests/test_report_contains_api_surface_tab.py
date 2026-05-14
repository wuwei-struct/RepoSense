import os
import tempfile
import unittest
from reposense.scan import run_scan


class ReportContainsApiSurfaceTabTest(unittest.TestCase):
    def test_report_contains_api_tab(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "api_surface_mix_min"))
        out = tempfile.mkdtemp(prefix="api_tab_run_")
        rd = run_scan(repo, out, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2")), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json")))
        with open(os.path.join(rd, "report.html"), "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("API Surface", html)


if __name__ == "__main__":
    unittest.main()

