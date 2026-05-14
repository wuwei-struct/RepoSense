import os, json, unittest
from reposense.scan import run_scan
from reposense.parsers.ast_treesitter import AST_AVAILABLE
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
class L3PyFastApiTest(unittest.TestCase):
    def test_fastapi_routes(self):
        rd = run_scan(fx("repos","l3_py_fastapi"), out_dir(), ruleset_dir(), budget_path())
        with open(os.path.join(rd, "report.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        l3_api = [f for f in data["findings"] if f["parse_level"] == "L3" and f["concept"] == "API"]
        l3_lock = [f for f in data["findings"] if f["parse_level"] == "L3" and f["concept"] == "Lock"]
        if not AST_AVAILABLE:
            self.assertEqual(len(l3_api), 0)
            self.assertEqual(len(l3_lock), 0)
        else:
            self.assertTrue(any("ping" in f["snippet"] for f in l3_api))
            self.assertTrue(len(l3_lock) >= 1)
