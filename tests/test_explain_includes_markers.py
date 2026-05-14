import os, json, sqlite3, unittest, sys, subprocess, tempfile
def specs_dir():
    return os.path.abspath("specs")
def rules_v2():
    return os.path.abspath(os.path.join("rulesets","specs_v2"))
def fx_repo():
    return os.path.abspath(os.path.join("tests","fixtures","repos","text_signals"))
def out_dir():
    return os.path.abspath(os.path.join("analysis_runs"))
class ExplainIncludesMarkersTest(unittest.TestCase):
    def test_explain_has_markers(self):
        subprocess.run([sys.executable, "-m", "reposense", "specs", "compile", "rulesets", "--specs", specs_dir(), "--out", rules_v2(), "--json"], stdout=subprocess.PIPE)
        rd = subprocess.run([sys.executable, "-m", "reposense", "scan", fx_repo(), "--out", out_dir(), "--ruleset", rules_v2(), "--budget", os.path.abspath(os.path.join("presets","default.json")), "--specs", specs_dir()], stdout=subprocess.PIPE).stdout.decode("utf-8").strip().splitlines()[-1]
        conn = sqlite3.connect(os.path.join(rd, "detections.sqlite"))
        c = conn.cursor()
        row = c.execute("select f.fid from findings f join evidence e on e.eid=f.primary_eid where replace(e.path,'\\','/') like '%text_signals/good_idempotency.py'").fetchone()
        try:
            conn.close()
        except:
            pass
        self.assertIsNotNone(row)
        fid = str(row[0])
        res = subprocess.run([sys.executable, "-m", "reposense", "explain", rd, "finding", fid, "--json"], stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertIn("markers_hit", data["summary"])
        self.assertIn("score", data["summary"])
