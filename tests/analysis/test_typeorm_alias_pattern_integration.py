import shutil
import unittest

from tests.analysis.test_typescript_import_graph_schema import (
    build_alias_run,
    load_json,
)


class TypeOrmAliasPatternIntegrationTest(unittest.TestCase):
    def test_covered_write_is_suppressed_but_mixed_write_is_retained(self):
        run_dir = build_alias_run()
        try:
            patterns = load_json(run_dir / "patterns.json")["patterns"]
            outside = [
                item
                for item in patterns
                if item.get("pattern_type") == "db_write_outside_tx"
            ]
            locations = {
                (
                    ref.get("file"),
                    ref.get("start_line"),
                )
                for item in outside
                for ref in (item.get("evidence_refs") or [])
            }
            self.assertNotIn(("src/user.repository.ts", 13), locations)
            self.assertTrue(
                any(
                    "partial_transaction_coverage"
                    in ((item.get("metadata") or {}).get("limitations") or [])
                    for item in outside
                )
            )
        finally:
            shutil.rmtree(run_dir.parent, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
