import os, subprocess, unittest, sys, json
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
class GatePolicyFailTest(unittest.TestCase):
    def test_gate_fail_exit_code(self):
        rd = run_scan(fx("repos","gate_fail"), out_dir(), ruleset_dir(), budget_path())
        with open(os.path.join(rd, "manifest.json"), "r", encoding="utf-8") as f:
            man = json.load(f)
        repo_root = man.get("repo_root")
        al = os.path.join(repo_root, ".reposense", "allowlist.json")
        if os.path.exists(al):
            try:
                os.remove(al)
            except:
                pass
        cmd = [sys.executable, "-m", "reposense", "gate", rd, "--policy", policy_path()]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(res.returncode, 2)
