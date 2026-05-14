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
class GraphEventsPresentTest(unittest.TestCase):
    def test_events_types_present(self):
        rd = run_scan(fx("repos","graph_mix"), out_dir(), ruleset_dir(), budget_path())
        with open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8") as f:
            g = json.load(f)
        types = set([n["type"] for n in g.get("nodes", [])])
        self.assertIn("api", types)
        self.assertIn("workflow", types)
        self.assertIn("service", types)
        self.assertIn("table", types)
        self.assertIn("index", types)
