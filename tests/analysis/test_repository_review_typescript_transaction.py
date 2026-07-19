import json
import shutil
import unittest

from reposense.analysis.review.review_export import (
    export_repository_review_report,
)
from tests.analysis._typescript_transaction_fixture import (
    build_typescript_transaction_run,
)


class RepositoryReviewTypeScriptTransactionTest(unittest.TestCase):
    def test_review_includes_typescript_summary(self):
        run_dir = build_typescript_transaction_run()
        try:
            result = export_repository_review_report(run_dir)
            with open(
                result["report_json_path"], "r", encoding="utf-8"
            ) as handle:
                report = json.load(handle)
            tx = report["transaction_review"]
            self.assertEqual(
                tx["typescript_typeorm_correlations"]["status"], "enabled"
            )
            self.assertGreater(
                tx["typescript_typeorm_correlations"]["total_correlations"], 0
            )
            with open(
                result["report_markdown_path"], "r", encoding="utf-8"
            ) as handle:
                self.assertIn(
                    "TypeScript callback / QueryRunner", handle.read()
                )
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
