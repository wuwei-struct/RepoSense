import json
import os
import shutil
import unittest

from reposense.analysis.review.review_export import export_repository_review_report
from tests.analysis._transaction_correlation_fixture import build_transaction_run


class RepositoryReviewWithTransactionCorrelationTest(unittest.TestCase):
    def test_review_includes_transaction_summary(self):
        run_dir = build_transaction_run()
        try:
            result = export_repository_review_report(run_dir)
            with open(result["report_json_path"], "r", encoding="utf-8") as handle:
                report = json.load(handle)
            tx = report["transaction_review"]
            self.assertEqual(tx["correlation_status"], "enabled")
            self.assertGreater(tx["transaction_correlations"]["total_correlations"], 0)
            with open(result["report_markdown_path"], "r", encoding="utf-8") as handle:
                markdown = handle.read()
            self.assertIn("Explicit covered correlations", markdown)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
