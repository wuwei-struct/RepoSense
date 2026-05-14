import os
import json
import tempfile
import subprocess
import sys
import unittest


class CiRunnerExitCodesTest(unittest.TestCase):
    def test_fail_and_pass(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "entrypoints_min"))
        out = tempfile.mkdtemp(prefix="ci_run_out_")
        gate_fail = os.path.join(out, "gate_fail.json")
        with open(gate_fail, "w", encoding="utf-8") as f:
            json.dump({"gate_id":"t","version":"1","rules":[{"metric":"skipped_ratio","op":">=","value":0.0,"level":"fail","message":"force fail"}]}, f)
        p_fail = subprocess.run([sys.executable, "-m", "reposense", "ci", "run", "--repo", repo, "--out", out, "--gate", gate_fail], capture_output=True, text=True)
        self.assertEqual(p_fail.returncode, 2)
        gate_pass = os.path.join(out, "gate_pass.json")
        with open(gate_pass, "w", encoding="utf-8") as f:
            json.dump({"gate_id":"t","version":"1","rules":[{"metric":"artifacts_missing_count","op":">","value":99999,"level":"fail","message":"never"}]}, f)
        p_pass = subprocess.run([sys.executable, "-m", "reposense", "ci", "run", "--repo", repo, "--out", out, "--gate", gate_pass], capture_output=True, text=True)
        self.assertEqual(p_pass.returncode, 0)


if __name__ == "__main__":
    unittest.main()
