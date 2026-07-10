import json
import os
import shutil
import unittest

from reposense.analysis.health.health_export import export_code_health
from reposense.analysis.review.review_export import export_repository_review_report
from tests._tmpdir import make_temp_dir


class CodeHealthIntegrationTest(unittest.TestCase):
    def test_code_health_then_repository_review(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "code_health_smoke_min"))
        run_dir = make_temp_dir(prefix="code_health_int_run_")
        try:
            with open(os.path.join(run_dir, "event_graph.json"), "w", encoding="utf-8") as f:
                json.dump({"nodes": [{"event_id": "e1", "type": "queue_dispatch", "meta": {"path": "src/service.ts", "start_line": 5}}], "edges": []}, f)
            export_code_health(run_dir, repo_path=repo)
            res = export_repository_review_report(run_dir)
            with open(res["report_json_path"], "r", encoding="utf-8") as f:
                report = json.load(f)
            self.assertEqual((report.get("code_health_review") or {}).get("status"), "enabled")
            self.assertGreaterEqual((report.get("code_health_review") or {}).get("total_findings") or 0, 1)
            self.assertTrue(any("Code health" in " ".join(x.get("reason") or []) or x.get("path") == "src/service.ts" for x in report.get("human_review_required") or []))
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

