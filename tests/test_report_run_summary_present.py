import os
import json
import tempfile
import unittest
from reposense.scan import run_scan


class ReportRunSummaryPresentTest(unittest.TestCase):
    def test_run_summary_present(self):
        repo = tempfile.mkdtemp(prefix="repo_sum_")
        # minimal python to produce events/findings
        with open(os.path.join(repo, "main.py"), "w", encoding="utf-8") as f:
            f.write("from fastapi import FastAPI\napp = FastAPI()\n@app.get('/hello')\ndef h():\n    return {}\n")
        out = tempfile.mkdtemp(prefix="out_sum_")
        rd = run_scan(repo, out, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2")), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json")))
        with open(os.path.join(rd, "report.json"), "r", encoding="utf-8") as f:
            rep = json.load(f)
        s = rep.get("run_summary") or {}
        self.assertIn("findings_count", s)
        self.assertIn("events_count", s)
        self.assertIn("graph_nodes", s)
        self.assertTrue(isinstance(s.get("skipped_files_by_reason", []), list))


if __name__ == "__main__":
    unittest.main()

