import os, unittest, json, subprocess, sys
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
class RulesCheckTest(unittest.TestCase):
    def test_rules_check_ok(self):
        cmd = [sys.executable, "-m", "reposense", "rules", "check", ruleset_dir(), "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertTrue(data["ok"])
