import os, unittest, json, subprocess, sys
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def fixtures_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos"))
class RulesCoverageTest(unittest.TestCase):
    def test_rules_coverage(self):
        cmd = [sys.executable, "-m", "reposense", "rules", "coverage", ruleset_dir(), "--fixtures", fixtures_dir(), "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertTrue("hits" in data)
