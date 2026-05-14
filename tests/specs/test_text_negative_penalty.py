import os, json, sqlite3, unittest, sys, subprocess
def specs_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "specs"))
def rules_v2():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rulesets", "specs_v2"))
def fx_repo():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "text_signals"))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "analysis_runs"))
class TextNegativePenaltyTest(unittest.TestCase):
    def test_negative_penalty_lowers_score(self):
        subprocess.run([sys.executable, "-m", "reposense", "specs", "compile", "rulesets", "--specs", specs_dir(), "--out", rules_v2(), "--json"], stdout=subprocess.PIPE)
        rd = subprocess.run([sys.executable, "-m", "reposense", "scan", fx_repo(), "--out", out_dir(), "--ruleset", rules_v2(), "--budget", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "presets", "default.json")), "--specs", specs_dir()], stdout=subprocess.PIPE).stdout.decode("utf-8").strip().splitlines()[-1]
        conn = sqlite3.connect(os.path.join(rd, "detections.sqlite"))
        c = conn.cursor()
        rows = c.execute("select f.meta_json, e.path from findings f join evidence e on e.eid=f.primary_eid where replace(e.path,'\\','/') like '%text_signals/good_with_negative.py'").fetchall()
        try:
            conn.close()
        except:
            pass
        self.assertTrue(len(rows) >= 1)
        m = json.loads(rows[0][0] or "{}")
        self.assertIn("score", m)
        self.assertLess(m["score"], 0.5)
