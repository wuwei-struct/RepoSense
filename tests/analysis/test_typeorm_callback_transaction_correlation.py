import shutil
import unittest

from tests.analysis._typescript_transaction_fixture import (
    build_typescript_transaction_run,
    load_typescript_correlations,
)


class TypeOrmCallbackTransactionCorrelationTest(unittest.TestCase):
    def test_callback_manager_aliases_are_covered(self):
        run_dir = build_typescript_transaction_run()
        try:
            rows = [
                item
                for item in load_typescript_correlations(run_dir)
                if item["target_file"] == "src/callbacks.ts"
            ]
            self.assertEqual(len(rows), 2)
            self.assertEqual(
                {item["transaction_mechanism"] for item in rows},
                {"typeorm_callback", "entity_manager_callback"},
            )
            self.assertTrue(
                all(item["coverage_status"] == "covered_explicit" for item in rows)
            )
            self.assertTrue(all(item["transaction_evidence_refs"] for item in rows))
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
