import os, re, json, unittest, sys, subprocess
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
class ContextBriefEidsExistTest(unittest.TestCase):
    def test_eids_exist(self):
        rd = subprocess.run([sys.executable, "-m", "reposense", "scan", fx("repos","graph_mix"), "--out", out_dir(), "--ruleset", ruleset_dir(), "--budget", budget_path()], stdout=subprocess.PIPE).stdout.decode("utf-8").strip().splitlines()[-1]
        brief_out = os.path.join(out_dir(), "brief_out3")
        subprocess.run([sys.executable, "-m", "reposense", "context", "brief", rd, "--out", brief_out])
        md = os.path.join(brief_out, "context_brief.md")
        txt = open(md, "r", encoding="utf-8").read()
        eids = sorted(set(re.findall(r"\\bE\\d+\\b", txt)))
        for e in eids:
            p = os.path.join(rd, "evidence", f"{e}.json")
            self.assertTrue(os.path.isfile(p))
