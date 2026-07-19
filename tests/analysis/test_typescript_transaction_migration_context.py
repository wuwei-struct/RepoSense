import shutil
import unittest

from tests.analysis._typescript_transaction_fixture import (
    build_typescript_transaction_run,
    load_typescript_correlations,
)


class TypeScriptTransactionMigrationContextTest(unittest.TestCase):
    def test_migration_without_explicit_scope_is_unknown(self):
        run_dir = build_typescript_transaction_run()
        try:
            row = next(
                item
                for item in load_typescript_correlations(run_dir)
                if "/migrations/" in f"/{item['target_file']}"
            )
            self.assertEqual(row["coverage_status"], "unknown")
            self.assertIn(
                "migration_transaction_policy_requires_confirmation",
                row["limitations"],
            )
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
