import unittest

from tests.analysis._typeorm_fixture import service_operations


class TypeOrmQueryRunnerTransactionsTest(unittest.TestCase):
    def test_query_runner_lifecycle_and_write(self):
        items = service_operations()
        tx_ops = {item["operation"] for item in items if item["kind"] == "db.transaction"}
        self.assertIn("startTransaction", tx_ops)
        self.assertIn("commitTransaction", tx_ops)
        writes = [item for item in items if item["transaction_context"] == "query_runner_explicit"]
        query_runner_writes = [
            item
            for item in writes
            if item["kind"] == "db.write"
            and item["receiver_kind"] == "query_runner"
        ]
        self.assertEqual(len(query_runner_writes), 1)
        self.assertEqual(
            query_runner_writes[0]["receiver_name"],
            "this.queryRunner.manager",
        )


if __name__ == "__main__":
    unittest.main()
