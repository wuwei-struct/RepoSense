import json
import os
import shutil
import unittest

from reposense.analysis.authz.authz_export import export_permission_auditor
from reposense.analysis.review.review_export import export_repository_review_report
from tests._tmpdir import make_temp_dir


class PermissionAuditorIntegrationTest(unittest.TestCase):
    def test_permission_then_repository_review(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "authz_smoke_min"))
        run_dir = make_temp_dir(prefix="authz_int_run_")
        try:
            res = export_permission_auditor(run_dir, repo_path=repo)
            for key in ["surface_path", "risks_path", "report_path", "human_review_path", "negative_test_plan_path"]:
                self.assertTrue(os.path.isfile(res[key]), key)
            review = export_repository_review_report(run_dir)
            with open(review["report_json_path"], "r", encoding="utf-8") as f:
                obj = json.load(f)
            self.assertEqual((obj.get("permission_review") or {}).get("status"), "enabled")
            self.assertGreater((obj.get("permission_review") or {}).get("total_risks") or 0, 0)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

