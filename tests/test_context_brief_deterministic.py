import os, hashlib, unittest, sys, subprocess
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
def sha(fp):
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        h.update(f.read())
    return h.hexdigest()
class ContextBriefDeterministicTest(unittest.TestCase):
    def test_brief_sha_stable(self):
        rd = subprocess.run([sys.executable, "-m", "reposense", "scan", fx("repos","graph_mix"), "--out", out_dir(), "--ruleset", ruleset_dir(), "--budget", budget_path()], stdout=subprocess.PIPE).stdout.decode("utf-8").strip().splitlines()[-1]
        b1 = os.path.join(out_dir(), "brief_out4")
        b2 = os.path.join(out_dir(), "brief_out5")
        subprocess.run([sys.executable, "-m", "reposense", "context", "brief", rd, "--out", b1])
        subprocess.run([sys.executable, "-m", "reposense", "context", "brief", rd, "--out", b2])
        s1 = sha(os.path.join(b1, "context_brief.md"))
        s2 = sha(os.path.join(b2, "context_brief.md"))
        self.assertEqual(s1, s2)
