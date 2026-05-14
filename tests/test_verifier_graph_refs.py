import os, json, unittest
from reposense.scan import run_scan
from reposense.verifier import verify
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
class VerifierGraphRefsTest(unittest.TestCase):
    def test_missing_evidence_detected(self):
        rd = run_scan(fx("repos","graph_mix"), out_dir(), ruleset_dir(), budget_path())
        with open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8") as f:
            g = json.load(f)
        any_ev = None
        for n in g.get("nodes", []):
            if n.get("evidence"):
                any_ev = n["evidence"][0]
                break
        self.assertIsNotNone(any_ev)
        p = os.path.join(rd, "evidence", f"{any_ev}.json")
        if os.path.exists(p):
            os.remove(p)
        res = verify(rd)
        self.assertFalse(res["ok"])
        self.assertTrue(any("graph node" in e or "graph edge" in e for e in res["errors"]))
