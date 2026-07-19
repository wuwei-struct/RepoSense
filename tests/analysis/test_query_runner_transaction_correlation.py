import shutil
import unittest

from tests.analysis._typescript_transaction_fixture import (
    build_typescript_transaction_run,
    load_typescript_correlations,
)


class QueryRunnerTransactionCorrelationTest(unittest.TestCase):
    def test_write_inside_start_and_commit_is_covered(self):
        run_dir = build_typescript_transaction_run()
        try:
            row = next(
                item
                for item in load_typescript_correlations(run_dir)
                if item["target_file"] == "src/query-runner.ts"
            )
            self.assertEqual(row["coverage_status"], "covered_explicit")
            self.assertEqual(row["transaction_mechanism"], "query_runner")
            self.assertEqual(row["transaction_evidence_refs"][0]["start_line"], 9)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
