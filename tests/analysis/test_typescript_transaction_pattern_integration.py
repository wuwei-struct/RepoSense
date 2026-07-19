import json
import os
import shutil
import unittest

from tests.analysis._typescript_transaction_fixture import (
    build_typescript_transaction_run,
)


class TypeScriptTransactionPatternIntegrationTest(unittest.TestCase):
    def test_covered_suppressed_and_partial_unknown_retained(self):
        run_dir = build_typescript_transaction_run()
        try:
            with open(
                os.path.join(run_dir, "patterns.json"),
                "r",
                encoding="utf-8",
            ) as handle:
                patterns = json.load(handle)["patterns"]
            rows = [
                item
                for item in patterns
                if item["pattern_type"] == "db_write_outside_tx"
            ]
            paths = {item["metadata"]["path"] for item in rows}
            self.assertNotIn("src/callbacks.ts", paths)
            self.assertNotIn("src/query-runner.ts", paths)
            self.assertIn("src/wrapper.ts", paths)
            self.assertIn(
                "partial_transaction_coverage",
                next(
                    item
                    for item in rows
                    if item["metadata"]["path"] == "src/wrapper.ts"
                )["metadata"]["limitations"],
            )
            self.assertTrue(all(item["status"] == "suspected" for item in rows))
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
