import json
import os
import unittest

from reposense.analysis.ai.explain_export import export_ai_explain
from reposense.analysis.ai.pattern_export import export_patterns
from reposense.analysis.ai.risks_export import export_ai_risks
from reposense.analysis.ai.summary_export import export_ai_summary
from reposense.report import build_report_html
from reposense.scan import run_scan
from tests._tmpdir import make_temp_dir


class StudioAIIntegrationTest(unittest.TestCase):
    def test_studio_ai_blocks_in_report(self):
        repo = make_temp_dir(prefix="repo_studio_ai_")
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
        out = make_temp_dir(prefix="out_studio_ai_")
        rd = run_scan(
            repo,
            out,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rulesets", "specs_v2")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "presets", "prod_lite.json")),
        )
        pres = export_patterns(rd)
        export_ai_summary(rd, write_json_file=True, write_markdown_file=True)
        export_ai_risks(rd, max_auto_drilldowns=3, severity_threshold="medium")
        with open(pres["patterns_path"], "r", encoding="utf-8") as f:
            pats = json.load(f).get("patterns") or []
        if pats:
            export_ai_explain(rd, "pattern", str(pats[0].get("pattern_id") or ""), with_drilldown=True)
        build_report_html(rd)
        with open(os.path.join(rd, "report.html"), "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("AI Summary", html)
        self.assertIn("Risks", html)
        self.assertIn("openExplainByPattern", html)
        self.assertIn("openSnippetByRequest", html)
        self.assertTrue(os.path.isfile(os.path.join(rd, "report.html")))
