import os
import tempfile
import unittest
import re

from reposense.ci import run_ci


class ReportBaselineDiffLinkTest(unittest.TestCase):
    def test_baseline_diff_not_clickable_when_missing(self):
        repo = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "api_json")
        )
        out = tempfile.mkdtemp(prefix="baseline_link_demo_")
        code = run_ci(repo, out, profile="demo", with_context_pack=False, json_stdout=False)
        self.assertIn(code, (0, 2))
        runs = [os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")]
        self.assertTrue(runs)
        run_dir = sorted(runs)[-1]
        with open(os.path.join(run_dir, "report.html"), "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("BASELINE DIFF: N/A", html)
        m = re.search(
            r'<div class="card" id="demo-tour-card".*?</div>\s*</div>',
            html,
            flags=re.S,
        )
        self.assertIsNotNone(m)
        demo_card = m.group(0)
        self.assertNotIn('href="baseline_diff.json"', demo_card)


if __name__ == "__main__":
    unittest.main()
