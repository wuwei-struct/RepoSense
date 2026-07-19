import unittest

from reposense.analysis.transactions.correlation_schema import make_correlation_id, validate_correlation


class TransactionCorrelationSchemaTest(unittest.TestCase):
    def test_schema_and_stable_id(self):
        calls = [{"file": "src/OrderService.java", "line": 12, "caller_method": "save"}]
        self.assertEqual(make_correlation_id("db-1", "OrderRepository", "save", calls), make_correlation_id("db-1", "OrderRepository", "save", calls))
        item = {
            "db_event_id": "db-1",
            "coverage_status": "covered_explicit",
            "confidence": 0.9,
            "repository_type": "OrderRepository",
            "operation": "save",
            "callsites": calls,
            "callsite_evidence_refs": [{"file": "src/OrderService.java", "start_line": 12, "end_line": 12}],
            "db_write_evidence_refs": [{"file": "src/JpaOrderRepository.java", "start_line": 8, "end_line": 8}],
        }
        self.assertEqual(validate_correlation(item), [])
        item["coverage_status"] = "proved_safe"
        self.assertIn("coverage_status invalid", validate_correlation(item))


if __name__ == "__main__":
    unittest.main()
