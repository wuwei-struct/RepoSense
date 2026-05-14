import os, unittest, sys, subprocess
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
class ContextBriefBuildTest(unittest.TestCase):
    def test_brief_md_exists(self):
        rd = subprocess.run([sys.executable, "-m", "reposense", "scan", fx("repos","graph_mix"), "--out", out_dir(), "--ruleset", ruleset_dir(), "--budget", budget_path()], stdout=subprocess.PIPE).stdout.decode("utf-8").strip().splitlines()[-1]
        brief_out = os.path.join(out_dir(), "brief_out")
        subprocess.run([sys.executable, "-m", "reposense", "context", "brief", rd, "--out", brief_out])
        md = os.path.join(brief_out, "context_brief.md")
        self.assertTrue(os.path.isfile(md))
        with open(md, "r", encoding="utf-8") as f:
            txt = f.read()
        self.assertIn("Repo Fingerprint", txt)
        self.assertIn("API Surface", txt)
