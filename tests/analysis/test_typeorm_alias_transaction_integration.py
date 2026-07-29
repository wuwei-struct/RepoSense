import shutil
import unittest

from tests.analysis.test_typescript_import_graph_schema import (
    build_alias_run,
    load_json,
)


class TypeOrmAliasTransactionIntegrationTest(unittest.TestCase):
    def test_resolved_callers_cover_and_partially_cover_exact_operations(self):
        run_dir = build_alias_run()
        try:
            rows = [
                item
                for item in load_json(
                    run_dir / "transaction_correlations.json"
                )["correlations"]
                if item.get("language") == "typescript"
            ]
            create = next(item for item in rows if item["target_method"] == "create")
            remove = next(item for item in rows if item["target_method"] == "remove")
            self.assertEqual(create["coverage_status"], "covered_explicit")
            self.assertEqual(remove["coverage_status"], "partially_covered")
            self.assertTrue(create["alias_resolution_ids"])
            self.assertGreaterEqual(len(create["callsite_evidence_refs"]), 4)
        finally:
            shutil.rmtree(run_dir.parent, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
