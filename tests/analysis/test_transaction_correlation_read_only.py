import json
import os
import shutil
import unittest

from tests.analysis._transaction_correlation_fixture import build_transaction_run


class TransactionCorrelationReadOnlyTest(unittest.TestCase):
    def test_read_only_is_not_write_coverage(self):
        run_dir = build_transaction_run()
        try:
            with open(os.path.join(run_dir, "transaction_correlations.json"), "r", encoding="utf-8") as handle:
                rows = json.load(handle)["correlations"]
            target = next(row for row in rows if row["db_write_file"] == "JpaReadOnlyRepository.java")
            self.assertEqual(target["coverage_status"], "read_only_transaction")
            self.assertIn("write_call_inside_read_only_transaction", target["limitations"])
            with open(os.path.join(run_dir, "patterns.json"), "r", encoding="utf-8") as handle:
                patterns = json.load(handle)["patterns"]
            pattern = next(row for row in patterns if "JpaReadOnlyRepository.java" in row["files"])
            self.assertEqual(pattern["status"], "suspected")
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
