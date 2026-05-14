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
def latest_run_dir(base):
    dirs = [d for d in os.listdir(base) if d.startswith("repo-")]
    dirs.sort()
    return os.path.join(base, dirs[-1])
class ScanSnapshotTest(unittest.TestCase):
    def test_scan_api_json(self):
        rd = run_scan(fixture_path("repos", "api_json"), out_dir(), ruleset_dir(), budget_path())
        self.assertTrue(os.path.exists(os.path.join(rd, "indices.sqlite")))
        self.assertTrue(os.path.exists(os.path.join(rd, "detections.sqlite")))
        self.assertTrue(os.path.exists(os.path.join(rd, "report.json")))
        self.assertTrue(os.path.exists(os.path.join(rd, "report.html")))
        self.assertTrue(os.path.exists(os.path.join(rd, "meta", "tool_version.json")))
        self.assertTrue(os.path.exists(os.path.join(rd, "meta", "ruleset_version.json")))
        with open(os.path.join(rd, "report.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertTrue(len(data["findings"]) >= 1)
        l2 = [f for f in data["findings"] if f["parse_level"] == "L2"]
        self.assertTrue(len(l2) >= 1)
        efile = os.path.join(rd, "evidence", f'E{l2[0]["primary_eid"]}.json')
        self.assertTrue(os.path.exists(efile))
    def test_scan_api_yaml(self):
        rd = run_scan(fixture_path("repos", "api_yaml"), out_dir(), ruleset_dir(), budget_path())
        with open(os.path.join(rd, "report.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        l2 = [f for f in data["findings"] if f["parse_level"] == "L2"]
        self.assertTrue(len(l2) >= 1)
    def test_scan_text_keywords(self):
        rd = run_scan(fixture_path("repos", "text_keywords"), out_dir(), ruleset_dir(), budget_path())
        with open(os.path.join(rd, "report.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        concepts = set([f["concept"] for f in data["findings"]])
        self.assertIn("Queue", concepts)
        self.assertIn("Cache", concepts)
        self.assertIn("FileSystem", concepts)

