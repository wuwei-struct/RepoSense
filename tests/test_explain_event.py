import os, json, unittest
from reposense.scan import run_scan
from reposense.explain import explain_event
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
class ExplainEventTest(unittest.TestCase):
    def test_explain_service_event(self):
        rd = run_scan(fx("repos","graph_mix"), out_dir(), ruleset_dir(), budget_path())
        with open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8") as f:
            g = json.load(f)
        svc = next((n for n in g.get("nodes", []) if n["type"] == "service"), None)
        self.assertIsNotNone(svc)
        info = explain_event(rd, svc["event_id"], True)
        self.assertTrue(len(info["evidence"]) >= 1)
        self.assertTrue(any("path" in e and "snippet" in e for e in info["evidence"]))
        inc = info["neighbors"]["outgoing_declares_dependency"]
        self.assertTrue(len(inc) >= 1)
