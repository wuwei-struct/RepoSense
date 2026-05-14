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
class GraphServiceDepsTest(unittest.TestCase):
    def test_service_declares_dependency(self):
        rd = run_scan(fx("repos","graph_mix"), out_dir(), ruleset_dir(), budget_path())
        with open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8") as f:
            g = json.load(f)
        nodes = g.get("nodes", [])
        edges = g.get("edges", [])
        has_infra = any(n["type"] in ["cache","queue","storage"] for n in nodes)
        self.assertTrue(has_infra)
        has_dep = any(e["type"] == "declares_dependency" for e in edges)
        self.assertTrue(has_dep)
