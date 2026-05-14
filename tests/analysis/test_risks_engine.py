import json
import os
import shutil
import unittest

from reposense.analysis.ai.risks_engine import generate_risks_report
from tests.analysis._drilldown_fixture import build_drilldown_run_dir


class RisksEngineTest(unittest.TestCase):
    def test_facts_only_mode(self):
        rd = build_drilldown_run_dir()
        try:
            obj = generate_risks_report(rd, no_drilldown=True)
            self.assertEqual(obj.get("mode"), "facts_only")
            self.assertTrue(len(obj.get("risk_items") or []) >= 1)
        finally:
            shutil.rmtree(rd, ignore_errors=True)

    def test_auto_drilldown_for_suspected_medium(self):
        rd = build_drilldown_run_dir()
        try:
            p = os.path.join(rd, "patterns.json")
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["patterns"][0]["status"] = "suspected"
            data["patterns"][0]["severity"] = "medium"
            data["patterns"][0]["evidence_refs"] = data["patterns"][0]["evidence_refs"][:1]
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f)
            obj = generate_risks_report(rd, max_auto_drilldowns=2, severity_threshold="medium")
            self.assertEqual(obj.get("mode"), "facts_plus_targeted_drilldown")
            self.assertGreaterEqual(int((obj.get("metadata") or {}).get("auto_drilldowns_used") or 0), 1)
        finally:
            shutil.rmtree(rd, ignore_errors=True)
