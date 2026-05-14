import os, json, unittest
from reposense.scan import run_scan
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
class ExportSarifTest(unittest.TestCase):
    def test_export_sarif(self):
        rd = run_scan(fx("repos","graph_mix"), out_dir(), ruleset_dir(), budget_path())
        outp = os.path.join(rd, "exports", "reposense.sarif.json")
        from reposense.sarif import export_sarif
        export_sarif(rd, outp)
        with open(outp, "r", encoding="utf-8") as f:
            sarif = json.load(f)
        self.assertEqual(sarif["version"], "2.1.0")
        runs = sarif.get("runs", [])
        self.assertTrue(len(runs) >= 1)
        results = runs[0].get("results", [])
        self.assertTrue(len(results) >= 1)
        for r in results:
            self.assertTrue("ruleId" in r)
            self.assertTrue("locations" in r and len(r["locations"]) >= 1)
            self.assertTrue("fingerprints" in r and "stable_finding_id" in r["fingerprints"])
