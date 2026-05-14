import os
import json
import unittest
def fixture_path(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def latest_run_dir(base):
    dirs = [d for d in os.listdir(base) if d.startswith("repo-")]
    dirs.sort()
    return os.path.join(base, dirs[-1])
class RuleLineRangesTest(unittest.TestCase):
    def test_rule_line_ranges_text(self):
        from reposense.scan import run_scan
        rd = run_scan(fixture_path("repos", "text_keywords"), out_dir(), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic")), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json")))
        with open(os.path.join(rd, "report.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        def ok(concept, expected_line):
            hits = [f for f in data["findings"] if f["concept"] == concept]
            return any(h["start_line"] <= expected_line <= h["end_line"] for h in hits)
        self.assertTrue(ok("Queue", 1))
        self.assertTrue(ok("Cache", 2))
        self.assertTrue(ok("FileSystem", 3))

