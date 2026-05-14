import os, json, sqlite3, unittest, sys, subprocess, tempfile
def specs_dir():
    return os.path.abspath("specs")
def rules_v2():
    return os.path.abspath(os.path.join("rulesets","specs_v2"))
def fx_repo():
    return os.path.abspath(os.path.join("tests","fixtures","repos","text_signals"))
def out_dir():
    return os.path.abspath(os.path.join("analysis_runs"))
class SarifContainsMarkersPropertiesTest(unittest.TestCase):
    def test_sarif_properties_has_markers(self):
        subprocess.run([sys.executable, "-m", "reposense", "specs", "compile", "rulesets", "--specs", specs_dir(), "--out", rules_v2(), "--json"], stdout=subprocess.PIPE)
        rd = subprocess.run([sys.executable, "-m", "reposense", "scan", fx_repo(), "--out", out_dir(), "--ruleset", rules_v2(), "--budget", os.path.abspath(os.path.join("presets","default.json")), "--specs", specs_dir()], stdout=subprocess.PIPE).stdout.decode("utf-8").strip().splitlines()[-1]
        outp = os.path.join(out_dir(), "out.sarif.json")
        subprocess.run([sys.executable, "-m", "reposense", "export", "sarif", rd, "--out", outp], stdout=subprocess.PIPE)
        sarif = json.load(open(outp, "r", encoding="utf-8"))
        runs = sarif.get("runs", [])
        self.assertTrue(len(runs) >= 1)
        results = runs[0].get("results", [])
        self.assertTrue(len(results) >= 1)
        props = results[0].get("properties", {})
        self.assertTrue("markers_hit" in props or "anti_patterns_hit" in props)
