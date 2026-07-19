import unittest

from reposense.analysis.ai.pattern_rules import rule_db_write_outside_tx


class TypeOrmPatternIntegrationTest(unittest.TestCase):
    def test_typeorm_write_without_explicit_context_is_suspected(self):
        ctx = {
            "events": [{
                "event_id": "N1",
                "type": "db_op",
                "meta": {
                    "db.kind": "db.write",
                    "framework": "typeorm",
                    "path": "src/users.ts",
                    "start_line": 10,
                    "end_line": 10,
                    "scope": {"kind": "method", "name": "save"},
                    "transaction_context": "unknown",
                },
            }],
            "evidence_by_id": {},
            "transaction_correlations": {},
        }
        patterns = rule_db_write_outside_tx(ctx)
        self.assertTrue(patterns)
        self.assertEqual(patterns[0]["status"], "suspected")
        self.assertIn(
            "typescript_transaction_coverage_unresolved",
            patterns[0]["metadata"]["limitations"],
        )


if __name__ == "__main__":
    unittest.main()
