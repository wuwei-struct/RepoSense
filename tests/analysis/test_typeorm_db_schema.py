import unittest

from reposense.analysis.db.typeorm_schema import normalize_operation, stable_operation_id


class TypeOrmDbSchemaTest(unittest.TestCase):
    def test_stable_id_and_required_fields(self):
        item = {
            "kind": "db.read", "operation": "find", "receiver_kind": "repository",
            "receiver_name": "users", "file": "src/users.ts", "line_start": 3,
        }
        self.assertEqual(stable_operation_id(item), stable_operation_id(dict(item)))
        normalized = normalize_operation(item)
        self.assertEqual(normalized["line_end"], 3)
        self.assertNotIn(":", normalized["file"][:2])


if __name__ == "__main__":
    unittest.main()
