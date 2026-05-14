import json
import os
import tempfile
import unittest

from reposense.scan import run_scan


class PatternEngineScanIntegrationTest(unittest.TestCase):
    def test_scan_emits_pattern_artifacts(self):
        repo = tempfile.mkdtemp(prefix="repo_pattern_scan_")
        with open(os.path.join(repo, "app.py"), "w", encoding="utf-8") as f:
            f.write(
                "from fastapi import FastAPI\n"
                "app = FastAPI()\n"
                "@app.post('/orders')\n"
                "def create_order():\n"
                "    pass\n"
            )
        out = tempfile.mkdtemp(prefix="out_pattern_scan_")
        rd = run_scan(
            repo,
            out,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rulesets", "specs_v2")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "presets", "prod_lite.json")),
        )
        self.assertTrue(os.path.isfile(os.path.join(rd, "patterns.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "pattern_summary.json")))
        cp_pat = os.path.join(rd, "context_pack", "ARTIFACTS", "patterns.json")
        cp_sum = os.path.join(rd, "context_pack", "ARTIFACTS", "pattern_summary.json")
        self.assertTrue(os.path.isfile(cp_pat))
        self.assertTrue(os.path.isfile(cp_sum))
        idx = json.load(open(os.path.join(rd, "context_pack", "MAP", "index.json"), "r", encoding="utf-8"))
        self.assertIn("patterns", idx.get("outputs") or {})
        self.assertIn("pattern_summary", idx.get("outputs") or {})

