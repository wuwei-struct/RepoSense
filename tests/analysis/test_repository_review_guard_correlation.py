import json
import os
import shutil
import unittest

from reposense.analysis.review.review_export import (
    export_repository_review_report,
)
from tests.analysis._guard_correlation_fixture import build_guard_run


class RepositoryReviewGuardCorrelationTest(unittest.TestCase):
    def test_review_reports_effective_guard_summary(self):
        run_dir, _result = build_guard_run()
        try:
            output = export_repository_review_report(run_dir)
            with open(
                output["report_json_path"], "r", encoding="utf-8"
            ) as handle:
                report = json.load(handle)
            guards = report["permission_review"]["guard_correlation"]
            self.assertEqual(guards["status"], "enabled")
            self.assertGreater(guards["protected_global"], 0)
            self.assertGreater(
                guards["intentional_public_bypasses"], 0
            )
            human = json.dumps(
                report["human_review_required"], ensure_ascii=False
            )
            self.assertNotIn("/auth/login", human)
            with open(
                output["report_markdown_path"], "r", encoding="utf-8"
            ) as handle:
                markdown = handle.read()
            self.assertIn("Guard protected method/controller/global", markdown)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
