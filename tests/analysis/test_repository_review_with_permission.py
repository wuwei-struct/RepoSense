import json
import os
import shutil
import unittest

from reposense.analysis.authz.authz_export import export_permission_auditor
from reposense.analysis.review.review_export import export_repository_review_report
from tests.analysis._ai_summary_fixture import build_ai_summary_run_dir


class RepositoryReviewWithPermissionTest(unittest.TestCase):
    def test_review_consumes_permission_artifacts(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "authz_smoke_min"))
        run_dir = build_ai_summary_run_dir()
        try:
            export_permission_auditor(run_dir, repo_path=repo)
            res = export_repository_review_report(run_dir)
            with open(res["report_json_path"], "r", encoding="utf-8") as f:
                report = json.load(f)
            self.assertEqual((report.get("permission_review") or {}).get("status"), "enabled")
            self.assertIn("Permission Review", report.get("sections") or [])
            with open(res["human_review_path"], "r", encoding="utf-8") as f:
                human_md = f.read()
            self.assertIn("authentication", human_md.lower())
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

