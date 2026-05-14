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
class L3JsExpressTest(unittest.TestCase):
    def test_express_routes(self):
        rd = run_scan(fx("repos","l3_js_express"), out_dir(), ruleset_dir(), budget_path())
        with open(os.path.join(rd, "report.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        l3 = [f for f in data["findings"] if f["parse_level"] == "L3" and f["concept"] == "API"]
        if not AST_AVAILABLE:
            self.assertEqual(len(l3), 0)
            with open(os.path.join(rd, "meta","config.json"), "r", encoding="utf-8") as mf:
                meta = json.load(mf)
            ws = meta.get("warnings", [])
            self.assertTrue(any(w.get("type") == "ast_disabled" for w in ws))
        else:
            self.assertTrue(any("hello" in f["snippet"] for f in l3))
