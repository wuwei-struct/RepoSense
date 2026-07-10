import json
import os
import shutil
import unittest

from reposense.analysis.ai.pattern_export import export_patterns
from reposense.analysis.ai.risks_export import export_ai_risks
from reposense.analysis.ai.summary_export import export_ai_summary
from reposense.analysis.reports.backend_verifier_report import export_backend_verifier_report
from reposense.analysis.review.review_export import export_repository_review_report
from reposense.scan import run_scan
from tests._tmpdir import make_temp_dir


class RepositoryReviewIntegrationTest(unittest.TestCase):
    def test_review_outputs_and_manifest(self):
        repo = make_temp_dir(prefix="repo_review_int_")
        out = make_temp_dir(prefix="out_review_int_")
        try:
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
            rd = run_scan(
                repo,
                out,
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rulesets", "specs_v2")),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "presets", "prod_lite.json")),
            )
            export_backend_verifier_report(rd)
            export_patterns(rd)
            export_ai_summary(rd, write_json_file=True, write_markdown_file=True)
            export_ai_risks(rd, no_drilldown=True)
            res = export_repository_review_report(rd)
            for key in ["report_json_path", "report_markdown_path", "risk_matrix_path", "human_review_path"]:
                self.assertTrue(os.path.isfile(res[key]), key)
            with open(res["report_json_path"], "r", encoding="utf-8") as f:
                obj = json.load(f)
            self.assertEqual(obj.get("report_type"), "repository_review_report")
            self.assertIn("Human Review Required", obj.get("sections") or [])
            with open(os.path.join(rd, "run_manifest.json"), "r", encoding="utf-8") as f:
                rm = json.load(f)
            paths = {x.get("path") for x in (rm.get("artifacts") or [])}
            self.assertIn("repository_review_report.json", paths)
            self.assertIn("repository_review_report.md", paths)
            self.assertIn("review_risk_matrix.json", paths)
            self.assertIn("human_review_required.md", paths)
        finally:
            shutil.rmtree(repo, ignore_errors=True)
            shutil.rmtree(out, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

