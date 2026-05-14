import json
import os
import shutil
import unittest

from reposense.analysis.ai.explain_engine import generate_explain_result
from tests.analysis._drilldown_fixture import build_drilldown_run_dir


class ExplainEngineTest(unittest.TestCase):
    def test_facts_only_for_finding(self):
        rd = build_drilldown_run_dir()
        try:
            obj = generate_explain_result(rd, "finding", "f-1")
            self.assertEqual(obj.get("mode"), "facts_only")
            self.assertTrue(len(obj.get("confirmed") or []) >= 1)
        finally:
            shutil.rmtree(rd, ignore_errors=True)

    def test_suspected_pattern_auto_drilldown(self):
        rd = build_drilldown_run_dir()
        try:
            p = os.path.join(rd, "patterns.json")
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["patterns"][0]["status"] = "suspected"
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f)
            obj = generate_explain_result(rd, "pattern", "pat-1")
            self.assertEqual(obj.get("mode"), "facts_plus_drilldown")
            self.assertTrue(obj.get("snippet_pack_ref"))
        finally:
            shutil.rmtree(rd, ignore_errors=True)

    def test_no_drilldown_flag(self):
        rd = build_drilldown_run_dir()
        try:
            obj = generate_explain_result(rd, "pattern", "pat-1", no_drilldown=True)
            self.assertEqual(obj.get("mode"), "facts_only")
            self.assertEqual(obj.get("snippet_pack_ref"), {})
        finally:
            shutil.rmtree(rd, ignore_errors=True)
