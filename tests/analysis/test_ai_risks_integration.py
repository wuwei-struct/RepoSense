import json
import os
import unittest

from reposense.analysis.ai.pattern_export import export_patterns
from reposense.analysis.ai.risks_export import export_ai_risks
from reposense.analysis.ai.summary_export import export_ai_summary
from reposense.scan import run_scan
from tests._tmpdir import make_temp_dir


class AIRisksIntegrationTest(unittest.TestCase):
    def test_risks_outputs_and_manifest(self):
        repo = make_temp_dir(prefix="repo_risks_int_")
        with open(os.path.join(repo, "app.py"), "w", encoding="utf-8") as f:
            f.write(
                "from fastapi import FastAPI\n"
                "app = FastAPI()\n"
                "@app.post('/orders')\n"
                "def create_order(payload):\n"
                "    save(payload)\n"
                "    send(payload)\n"
                "    return {'ok': True}\n"
            )
        out = make_temp_dir(prefix="out_risks_int_")
        rd = run_scan(
            repo,
            out,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rulesets", "specs_v2")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "presets", "prod_lite.json")),
        )
        export_patterns(rd)
        export_ai_summary(rd, write_json_file=True, write_markdown_file=True)
        res = export_ai_risks(rd, max_auto_drilldowns=3, severity_threshold="medium")
        self.assertTrue(os.path.isfile(res["json_path"]))
        self.assertTrue(os.path.isfile(res["markdown_path"]))
        with open(res["json_path"], "r", encoding="utf-8") as f:
            obj = json.load(f)
        self.assertTrue(isinstance(obj.get("risk_items"), list))
        self.assertTrue(os.path.isfile(os.path.join(rd, "run_manifest.json")))
        with open(os.path.join(rd, "run_manifest.json"), "r", encoding="utf-8") as f:
            rm = json.load(f)
        paths = set([x.get("path") for x in (rm.get("artifacts") or [])])
        self.assertIn("ai_risks/risks.json", paths)
        self.assertIn("ai_risks/risks.md", paths)
