import shutil
import unittest

from tests.analysis._typescript_transaction_fixture import (
    build_typescript_transaction_run,
    load_typescript_correlations,
)


class TypeScriptTransactionMixedCallersTest(unittest.TestCase):
    def test_mixed_callers_are_partial(self):
        run_dir = build_typescript_transaction_run()
        try:
            row = next(
                item
                for item in load_typescript_correlations(run_dir)
                if item["target_method"] == "mixedStore"
            )
            self.assertEqual(row["coverage_status"], "partially_covered")
            self.assertIn("partial_transaction_coverage", row["limitations"])
            self.assertEqual(len(row["callsites"]), 2)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
