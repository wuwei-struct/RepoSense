import os
import json
import unittest
from reposense.scan import run_scan
def fixture_path(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
class L2GhaExtractTest(unittest.TestCase):
    def test_gha_l2_findings(self):
        rd = run_scan(fixture_path("repos", "gha_workflow"), out_dir(), ruleset_dir(), budget_path())
        with open(os.path.join(rd, "report.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        l2 = [f for f in data["findings"] if f["parse_level"] == "L2"]
        concepts = set([f["concept"] for f in l2])
        self.assertTrue("Scheduling" in concepts or "Secrets/Config" in concepts or "External IO" in concepts)
