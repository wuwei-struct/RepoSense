import unittest

from tests.analysis._typeorm_fixture import service_operations


class TypeOrmRawSqlClassificationTest(unittest.TestCase):
    def test_static_and_dynamic_sql(self):
        queries = [item for item in service_operations() if item["operation"] == "query"]
        self.assertTrue(any(item["kind"] == "db.read" for item in queries))
        self.assertTrue(any(item["kind"] == "db.write" for item in queries))
        self.assertGreaterEqual(
            sum(item["kind"] == "db.write" for item in queries),
            2,
        )
        unknown = [item for item in queries if item["kind"] == "db.query_unknown"]
        self.assertTrue(unknown)
        self.assertIn("dynamic_sql_operation_unresolved", unknown[0]["limitations"])


if __name__ == "__main__":
    unittest.main()
