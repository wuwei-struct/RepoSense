import shutil
import unittest

from tests.analysis._typescript_transaction_fixture import (
    build_typescript_transaction_run,
    load_typescript_correlations,
)


class TypeScriptTransactionDecoratorProvenanceTest(unittest.TestCase):
    def test_trusted_method_and_class_but_not_untrusted_name(self):
        run_dir = build_typescript_transaction_run()
        try:
            rows = [
                item
                for item in load_typescript_correlations(run_dir)
                if item["target_file"] == "src/decorators.ts"
            ]
            by_operation = {item["operation"]: item for item in rows}
            self.assertEqual(
                by_operation["save"]["transaction_mechanism"],
                "trusted_decorator_method",
            )
            self.assertEqual(
                by_operation["insert"]["transaction_mechanism"],
                "trusted_decorator_class",
            )
            self.assertEqual(by_operation["delete"]["coverage_status"], "unknown")
            self.assertIn(
                "transaction_decorator_provenance_unresolved",
                by_operation["delete"]["limitations"],
            )
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
