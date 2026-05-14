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
class GraphIdsStableTest(unittest.TestCase):
    def test_ids_stable_across_scans(self):
        rd1 = run_scan(fx("repos","graph_mix"), out_dir(), ruleset_dir(), budget_path())
        with open(os.path.join(rd1, "event_graph.json"), "r", encoding="utf-8") as f1:
            g1 = json.load(f1)
        rd2 = run_scan(fx("repos","graph_mix"), out_dir(), ruleset_dir(), budget_path())
        with open(os.path.join(rd2, "event_graph.json"), "r", encoding="utf-8") as f2:
            g2 = json.load(f2)
        n1 = set([n["event_id"] for n in g1.get("nodes", [])])
        n2 = set([n["event_id"] for n in g2.get("nodes", [])])
        e1 = set([e["edge_id"] for e in g1.get("edges", [])])
        e2 = set([e["edge_id"] for e in g2.get("edges", [])])
        self.assertEqual(n1, n2)
        self.assertEqual(e1, e2)
