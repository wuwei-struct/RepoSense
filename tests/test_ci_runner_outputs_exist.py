import os
import json
import tempfile
import subprocess
import sys
import unittest


class CiRunnerOutputsExistTest(unittest.TestCase):
    def test_outputs_exist(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "entrypoints_min"))
        out = tempfile.mkdtemp(prefix="ci_run_out_exist_")
        p = subprocess.run([sys.executable, "-m", "reposense", "ci", "run", "--repo", repo, "--out", out], capture_output=True, text=True)
        self.assertIn(p.returncode, (0,2))
        # find the latest run dir under out
        runs = [os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")]
        self.assertTrue(len(runs) >= 1)
        rd = sorted(runs)[-1]
        report = os.path.join(rd, "report.json")
        sarif = os.path.join(rd, "exports", "report.sarif.json")
        gate = os.path.join(rd, "quality_gate.json")
        ci = os.path.join(rd, "ci_summary.json")
        for pth in (report, sarif, gate, ci):
            self.assertTrue(os.path.isfile(pth))
            self.assertGreater(os.path.getsize(pth), 0)
        s = json.load(open(sarif, "r", encoding="utf-8"))
        props = ((s.get("runs") or [{}])[0].get("properties") or {})
        self.assertIsNotNone(props.get("reposense.gate_status"))


if __name__ == "__main__":
    unittest.main()
