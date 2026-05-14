import os, unittest, subprocess, sys
from reposense.scan import run_scan
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
def policy_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "policies", "default.json"))
class SelfcheckGateFailTest(unittest.TestCase):
    def test_selfcheck_gate_fail(self):
        rd = run_scan(fx("repos","gate_fail"), out_dir(), ruleset_dir(), budget_path())
        cmd = [sys.executable, "-m", "reposense", "selfcheck", rd, "--policy", policy_path()]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        self.assertEqual(res.returncode, 2)
