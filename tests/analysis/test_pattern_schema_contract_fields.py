import json
import unittest


class PatternSchemaContractFieldsTest(unittest.TestCase):
    def test_schema_has_required_fields(self):
        with open("schemas/pattern.schema.json", "r", encoding="utf-8-sig") as f:
            schema = json.load(f)

        self.assertEqual(schema.get("type"), "object")
        required = set(schema.get("required") or [])
        expected = {
            "rule_id",
            "category",
            "severity",
            "language",
            "signals",
            "evidence_required",
            "confidence_policy",
            "public_description",
            "commercial_insight_reserved",
        }
        self.assertTrue(expected.issubset(required))

        props = schema.get("properties") or {}
        for k in expected:
            self.assertIn(k, props)

    def test_minimal_example_shape(self):
        sample = {
            "rule_id": "db_write_outside_tx",
            "category": "transaction",
            "severity": "warning",
            "language": "python",
            "signals": ["db_write", "transaction_boundary_absent"],
            "evidence_required": True,
            "confidence_policy": "conservative",
            "public_description": "Detects database write signals without an observed transaction boundary.",
            "commercial_insight_reserved": True,
        }
        self.assertTrue(isinstance(sample["signals"], list))
        self.assertTrue(isinstance(sample["evidence_required"], bool))


if __name__ == "__main__":
    unittest.main()
