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
class IncrementalScanReuseTest(unittest.TestCase):
    def test_incremental_base(self):
        runA = run_scan(fx("repos","graph_mix"), out_dir(), ruleset_dir(), budget_path())
        runB = run_scan(fx("repos","graph_mix_v2"), out_dir(), ruleset_dir(), budget_path(), base_run_dir=runA)
        with open(os.path.join(runB, "meta", "config.json"), "r", encoding="utf-8") as f:
            meta = json.load(f)
        inc = meta.get("incremental", {})
        self.assertTrue(inc.get("skipped_count", 0) >= 1)
