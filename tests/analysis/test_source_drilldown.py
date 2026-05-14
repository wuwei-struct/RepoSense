import json
import os
import shutil
import unittest

from reposense.analysis.ai.source_drilldown import generate_snippet_pack
from tests.analysis._drilldown_fixture import build_drilldown_run_dir


class SourceDrilldownTest(unittest.TestCase):
    def test_pattern_drilldown_pack(self):
        rd = build_drilldown_run_dir()
        try:
            pack = generate_snippet_pack(
                rd,
                "pattern",
                "pat-1",
                budget={"context_lines": 2, "max_snippets": 4, "max_total_chars": 4000},
            )
            self.assertEqual(pack["target_type"], "pattern")
            self.assertEqual(pack["target_id"], "pat-1")
            self.assertTrue(len(pack["selected_snippets"]) >= 1)
            self.assertTrue(all(str(x.get("why_selected") or "") for x in pack["selected_snippets"]))
            self.assertTrue(all(isinstance(x.get("source_refs"), list) for x in pack["selected_snippets"]))
        finally:
            shutil.rmtree(rd, ignore_errors=True)

    def test_missing_file_limitation(self):
        rd = build_drilldown_run_dir()
        try:
            p = os.path.join(rd, "patterns.json")
            with open(p, "r", encoding="utf-8") as f:
                obj = json.load(f)
            obj["patterns"][0]["evidence_refs"].append(
                {"source_type": "finding", "finding_id": "f-x", "file": "svc/missing.py", "start_line": 1, "end_line": 1}
            )
            with open(p, "w", encoding="utf-8") as f:
                json.dump(obj, f)
            pack = generate_snippet_pack(rd, "pattern", "pat-1")
            txt = "\n".join(pack.get("limitations") or [])
            self.assertIn("File not readable or missing", txt)
        finally:
            shutil.rmtree(rd, ignore_errors=True)
