import json
import os
import tempfile
import unittest

from reposense.scan import run_scan
from reposense.analysis.ai.pattern_export import export_patterns
from reposense.analysis.ai.summary_export import export_ai_summary


class AISummaryScanIntegrationTest(unittest.TestCase):
    def test_scan_patterns_summary_integration(self):
        repo = tempfile.mkdtemp(prefix="repo_ai_summary_int_")
        with open(os.path.join(repo, "app.py"), "w", encoding="utf-8") as f:
            f.write(
                "from fastapi import FastAPI\n"
                "app = FastAPI()\n"
                "@app.post('/orders')\n"
                "def create_order():\n"
                "    return {'ok': True}\n"
            )
        out = tempfile.mkdtemp(prefix="out_ai_summary_int_")
        rd = run_scan(
            repo,
            out,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rulesets", "specs_v2")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "presets", "prod_lite.json")),
        )
        export_patterns(rd)
        export_ai_summary(rd, write_json_file=True, write_markdown_file=True)
        self.assertTrue(os.path.isfile(os.path.join(rd, "ai_summary.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "ai_summary.md")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "context_pack", "ARTIFACTS", "ai_summary.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "context_pack", "ARTIFACTS", "ai_summary.md")))
        with open(os.path.join(rd, "run_manifest.json"), "r", encoding="utf-8") as f:
            rm = json.load(f)
        paths = set([x.get("path") for x in (rm.get("artifacts") or [])])
        self.assertIn("ai_summary.json", paths)
        self.assertIn("ai_summary.md", paths)
