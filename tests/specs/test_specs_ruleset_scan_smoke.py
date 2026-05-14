import os, json, unittest, sys, subprocess
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "analysis_runs"))
class SpecsRulesetScanSmokeTest(unittest.TestCase):
    def test_scan_with_specs_v2_produces_L2(self):
        # compile latest specs to rulesets/specs_v2
        res1 = subprocess.run([sys.executable, "-m", "reposense", "specs", "compile", "rulesets", "--specs", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "specs")), "--out", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rulesets", "specs_v2")), "--json"], stdout=subprocess.PIPE)
        data1 = json.loads(res1.stdout.decode("utf-8"))
        self.assertTrue(data1["ok"])
        # scan graph_mix using specs_v2
        res2 = subprocess.run([sys.executable, "-m", "reposense", "scan", fx("repos","graph_mix"), "--out", out_dir(), "--ruleset", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rulesets", "specs_v2")), "--budget", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "presets", "default.json"))], stdout=subprocess.PIPE)
        rd = res2.stdout.decode("utf-8").strip().splitlines()[-1]
        # count L2 findings via detections.sqlite
        import sqlite3
        conn = sqlite3.connect(os.path.join(rd, "detections.sqlite"))
        c = conn.cursor()
        rows = c.execute("select count(1) from findings f join evidence e on e.eid=f.primary_eid where e.parse_level='L2'").fetchone()
        count_l2 = rows[0] if rows else 0
        conn.close()
        if count_l2 < 1:
            # enrich failure message
            rep = json.load(open(os.path.join(rd, "report.json"), "r", encoding="utf-8"))
            ruleset_version = rep.get("ruleset_version")
            meta = json.load(open(os.path.join(rd, "meta", "config.json"), "r", encoding="utf-8"))
            warns = meta.get("warnings", [])
            self.fail(f"L2 findings=0; ruleset_version={ruleset_version}; warnings_top={warns[:5]}")
        self.assertGreaterEqual(count_l2, 1)
