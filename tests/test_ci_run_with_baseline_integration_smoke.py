import os
import json
import tempfile
import subprocess
import sys
import unittest


class CiRunWithBaselineIntegrationSmokeTest(unittest.TestCase):
    def test_ci_run_baseline_smoke(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "entrypoints_min"))
        out = tempfile.mkdtemp(prefix="ci_run_base_smoke_")
        # first run to produce baseline
        p1 = subprocess.run([sys.executable,"-m","reposense","ci","run","--repo", repo, "--out", out, "--baseline-out", os.path.join(out,"baseline.json")], capture_output=True, text=True)
        self.assertIn(p1.returncode, (0,2))
        # second run with baseline-in
        p2 = subprocess.run([sys.executable,"-m","reposense","ci","run","--repo", repo, "--out", out, "--baseline-in", os.path.join(out,"baseline.json")], capture_output=True, text=True)
        self.assertIn(p2.returncode, (0,2))
        # locate latest run dir
        runs = [os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")]
        self.assertTrue(len(runs) >= 1)
        rd = sorted(runs)[-1]
        q = os.path.join(rd, "quality_gate.json")
        data = json.load(open(q, "r", encoding="utf-8"))
        self.assertTrue(data.get("baseline_used"))
        reg = data.get("regressions", {})
        self.assertIn("total", reg)


if __name__ == "__main__":
    unittest.main()
