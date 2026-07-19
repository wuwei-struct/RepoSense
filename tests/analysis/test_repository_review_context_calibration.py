import json
import os
import unittest

from reposense.analysis.authz.authz_export import export_permission_auditor
from reposense.analysis.health.health_export import export_code_health
from reposense.analysis.review.review_export import export_repository_review_report
from tests.analysis._review_context_fixture import build_context_run, fixture_repo


class RepositoryReviewContextCalibrationTest(unittest.TestCase):
    def test_review_separates_raw_and_actionable_items(self):
        run_dir = build_context_run()
        export_code_health(run_dir, repo_path=fixture_repo())
        export_permission_auditor(run_dir, repo_path=fixture_repo())
        result = export_repository_review_report(run_dir)
        with open(result["report_json_path"], "r", encoding="utf-8") as handle:
            report = json.load(handle)

        context = report["context_calibration"]
        self.assertGreaterEqual(context["public_auth_route_count"], 3)
        self.assertGreaterEqual(context["findings_excluded_from_primary_review_count"], 3)
        self.assertGreater(
            context["raw_code_health_findings"],
            context["actionable_code_health_risks"],
        )
        self.assertGreater(
            context["raw_permission_risks"],
            context["actionable_permission_risks"],
        )
        human_items = report["human_review_required"]
        human_text = json.dumps(human_items)
        public_login_refs = [
            ref
            for item in human_items
            for ref in (item.get("evidence_refs") or [])
            if ref.get("snippet") == '@Post("/auth/login")'
        ]
        self.assertEqual(public_login_refs, [])
        self.assertNotIn("src/database/seeds/demo.seed.ts", human_text)
        self.assertIn("src/services/order.service.ts", human_text)
        self.assertTrue(os.path.isfile(result["human_review_path"]))


if __name__ == "__main__":
    unittest.main()
