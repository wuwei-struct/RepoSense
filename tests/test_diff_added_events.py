import os, json, unittest
from reposense.scan import run_scan
from reposense.diff import diff_runs
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
class DiffAddedEventsTest(unittest.TestCase):
    def test_diff_between_runs(self):
        runA = run_scan(fx("repos","graph_mix"), out_dir(), ruleset_dir(), budget_path())
        runB = run_scan(fx("repos","graph_mix_v2"), out_dir(), ruleset_dir(), budget_path())
        res = diff_runs(runA, runB)
        self.assertTrue(res["ok"])
        added_events = res["events"]["added"]
        added_edges = res["edges"]["added"]
        self.assertTrue(len(added_events) >= 1 or len(added_edges) >= 1)
        # check findings stable id format
        for f in res["findings"]["added"]:
            self.assertEqual(len(f["stable_id"]), 12)
