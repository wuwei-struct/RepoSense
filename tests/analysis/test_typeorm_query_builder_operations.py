import unittest

from tests.analysis._typeorm_fixture import service_operations


class TypeOrmQueryBuilderOperationsTest(unittest.TestCase):
    def test_read_and_executed_writes_only(self):
        items = [item for item in service_operations() if item["receiver_kind"] == "query_builder"]
        self.assertTrue(any(item["operation"] == "getMany" and item["kind"] == "db.read" for item in items))
        self.assertTrue(any(item["operation"] == "update" and item["kind"] == "db.write" for item in items))
        self.assertTrue(any(item["operation"] == "delete" and item["kind"] == "db.write" for item in items))
        self.assertEqual(sum(item["operation"] == "update" for item in items), 1)


if __name__ == "__main__":
    unittest.main()
