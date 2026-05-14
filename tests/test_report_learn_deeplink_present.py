import os, unittest
from reposense.scan import run_scan
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
class ReportLearnDeepLinkTest(unittest.TestCase):
    def test_deeplink_present(self):
        rd = run_scan(fx("repos","graph_mix"), out_dir(), ruleset_dir(), budget_path())
        with open(os.path.join(rd, "report.html"), "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("Learn more about", html)
        self.assertIn("concepts/", html)
