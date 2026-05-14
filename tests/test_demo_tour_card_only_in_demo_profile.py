import os
import tempfile
import unittest
from reposense.ci import run_ci


class DemoTourCardOnlyInDemoProfileTest(unittest.TestCase):
    def test_card_present_in_demo(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "api_json"))
        out = tempfile.mkdtemp(prefix="tour_demo_")
        code = run_ci(repo, out, profile="demo", with_context_pack=False, json_stdout=False)
        self.assertIn(code, (0,2))
        rd = sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]
        html = open(os.path.join(rd, "report.html"), "r", encoding="utf-8").read()
        self.assertIn("REPOSENSE_DEMO_TOUR_CARD", html)
    def test_card_absent_in_prod_lite(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "api_json"))
        out = tempfile.mkdtemp(prefix="tour_prod_")
        code = run_ci(repo, out, profile="prod_lite", with_context_pack=False, json_stdout=False)
        self.assertIn(code, (0,2))
        rd = sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]
        html = open(os.path.join(rd, "report.html"), "r", encoding="utf-8").read()
        self.assertNotIn("REPOSENSE_DEMO_TOUR_CARD", html)


if __name__ == "__main__":
    unittest.main()
