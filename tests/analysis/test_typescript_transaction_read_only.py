import shutil
import unittest

from tests.analysis._typescript_transaction_fixture import (
    build_typescript_transaction_run,
    load_typescript_correlations,
)


class TypeScriptTransactionReadOnlyTest(unittest.TestCase):
    def test_read_only_write_is_not_covered(self):
        run_dir = build_typescript_transaction_run()
        try:
            row = next(
                item
                for item in load_typescript_correlations(run_dir)
                if item["operation"] == "update"
                and item["target_file"] == "src/decorators.ts"
            )
            self.assertEqual(row["coverage_status"], "read_only_transaction")
            self.assertIn(
                "write_call_inside_read_only_transaction", row["limitations"]
            )
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
