import unittest

from tests.analysis._typeorm_fixture import service_operations


class TypeOrmRepositoryOperationsTest(unittest.TestCase):
    def test_injected_repository_reads_and_writes(self):
        items = service_operations()
        operations = {(item["receiver_name"], item["operation"], item["kind"]) for item in items}
        self.assertIn(("this.users", "findOne", "db.read"), operations)
        self.assertIn(("this.users", "save", "db.write"), operations)
        self.assertIn(("this.users", "update", "db.write"), operations)
        self.assertIn(("this.users", "delete", "db.write"), operations)


if __name__ == "__main__":
    unittest.main()
