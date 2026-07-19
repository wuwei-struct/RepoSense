import shutil
import unittest

from tests.analysis._typescript_transaction_fixture import (
    build_typescript_transaction_run,
    load_typescript_correlations,
)


class TypeScriptTransactionWrapperCorrelationTest(unittest.TestCase):
    def test_one_hop_trusted_caller_covers_wrapper_write(self):
        run_dir = build_typescript_transaction_run()
        try:
            row = next(
                item
                for item in load_typescript_correlations(run_dir)
                if item["target_file"] == "src/wrapper.ts"
                and item["target_method"] == "store"
            )
            self.assertEqual(row["coverage_status"], "covered_explicit")
            self.assertEqual(
                row["transaction_mechanism"], "direct_wrapper_caller"
            )
            self.assertEqual(row["caller_class"], "TransactionalCaller")
            self.assertTrue(row["callsite_evidence_refs"])
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
