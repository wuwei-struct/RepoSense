import json
import shutil
import unittest

from reposense.analysis.review.review_export import (
    export_repository_review_report,
)
from tests.analysis._route_decorator_fixture import build_decorator_run


class RepositoryReviewRouteDecoratorSummaryTest(unittest.TestCase):
    def test_review_reports_decorator_classification_summary(self):
        run_dir, _result = build_decorator_run()
        try:
            output = export_repository_review_report(run_dir)
            with open(
                output["report_json_path"],
                "r",
                encoding="utf-8",
            ) as handle:
                report = json.load(handle)
            summary = report["api_surface_review"][
                "route_decorator_classification"
            ]
            self.assertEqual(summary["status"], "enabled")
            self.assertEqual(summary["accepted_route_count"], 8)
            self.assertGreater(summary["rejected_non_route_count"], 0)
            human = json.dumps(
                report["human_review_required"],
                ensure_ascii=False,
            )
            self.assertNotIn("DeleteDateColumn", human)
            self.assertNotIn("order.entity.ts", human)
            with open(
                output["report_markdown_path"],
                "r",
                encoding="utf-8",
            ) as handle:
                self.assertIn(
                    "Route decorators accepted / rejected / unknown",
                    handle.read(),
                )
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
