import os
import json
import tempfile
import unittest
from reposense.ci import run_ci
from reposense.baseline import save_baseline, compute_diff


class DemoBaselineDiffSmokeTest(unittest.TestCase):
    def test_baseline_and_diff(self):
        base_repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "demo_showcase"))
        reg_repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "demo_showcase_regress"))
        out = tempfile.mkdtemp(prefix="demo_diff_")
        code1 = run_ci(base_repo, out, profile="demo", with_context_pack=False, json_stdout=False)
        self.assertIn(code1, (0,2))
        rd1 = sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]
        bl = os.path.join(out, "baseline.json")
        save_baseline(rd1, bl, profile="demo", ruleset=os.path.abspath(os.path.join(os.path.dirname(__file__), "..","rulesets","demo_v1")), gate_id="demo")
        code2 = run_ci(reg_repo, out, profile="demo", with_context_pack=False, json_stdout=False)
        self.assertIn(code2, (0,2))
        rd2 = sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]
        dj = os.path.join(rd2, "baseline_diff.json")
        dm = os.path.join(rd2, "baseline_diff.md")
        compute_diff(bl, rd2, dj, out_md_path=dm, current_ruleset_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), "..","rulesets","demo_v1")))
        self.assertTrue(os.path.isfile(dj))
        self.assertTrue(os.path.isfile(dm))


if __name__ == "__main__":
    unittest.main()
