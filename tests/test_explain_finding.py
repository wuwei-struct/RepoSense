import os, sqlite3, unittest
from reposense.scan import run_scan
from reposense.explain import explain_finding
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
class ExplainFindingTest(unittest.TestCase):
    def test_explain_any_finding(self):
        rd = run_scan(fx("repos","graph_mix"), out_dir(), ruleset_dir(), budget_path())
        conn = sqlite3.connect(os.path.join(rd, "detections.sqlite"))
        c = conn.cursor()
        row = c.execute("select fid from findings limit 1").fetchone()
        conn.close()
        self.assertIsNotNone(row)
        fid = row[0]
        info = explain_finding(rd, fid, True)
        self.assertTrue(len(info["evidence"]) >= 1)
        for e in info["evidence"]:
            self.assertTrue(e["start_line"] <= e["end_line"])
