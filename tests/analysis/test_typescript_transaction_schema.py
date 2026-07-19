import unittest

from reposense.analysis.transactions.correlation_schema import (
    normalize_correlation,
    validate_correlation,
)


class TypeScriptTransactionSchemaTest(unittest.TestCase):
    def test_typescript_fields_and_mechanism(self):
        item = normalize_correlation(
            {
                "db_event_id": "event-1",
                "db_operation_id": "typeorm-1",
                "language": "typescript",
                "framework": "typeorm",
                "coverage_status": "covered_explicit",
                "transaction_mechanism": "typeorm_callback",
                "confidence": 0.9,
                "callsite_evidence_refs": [
                    {"file": "src/a.ts", "start_line": 4, "end_line": 4}
                ],
                "db_write_evidence_refs": [
                    {"file": "src/a.ts", "start_line": 4, "end_line": 4}
                ],
            }
        )
        self.assertEqual(item["language"], "typescript")
        self.assertEqual(validate_correlation(item), [])
        item["transaction_mechanism"] = "runtime_magic"
        self.assertIn("transaction_mechanism invalid", validate_correlation(item))


if __name__ == "__main__":
    unittest.main()
