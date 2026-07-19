import unittest

from reposense.parsers.typescript_minimal import detect_ts_typeorm_transactions
from tests.analysis._typeorm_fixture import FIXTURE, service_operations


class TypeOrmManagerDataSourceOperationsTest(unittest.TestCase):
    def test_get_repository_and_callback_manager(self):
        items = service_operations()
        self.assertTrue(any(item["receiver_name"] == "repo" and item["operation"] == "find" for item in items))
        callback = [item for item in items if item["receiver_name"] == "manager" and item["operation"] == "save"]
        self.assertTrue(callback)
        self.assertEqual(callback[0]["transaction_context"], "explicit_callback")
        lines = (FIXTURE / "src" / "user.service.ts").read_text(
            encoding="utf-8"
        ).splitlines()
        transactions = detect_ts_typeorm_transactions(lines)
        data_source_transactions = [
            item
            for item in transactions
            if item.get("callee_expr") == "this.dataSource.transaction"
        ]
        self.assertEqual(len(data_source_transactions), 1)
        self.assertEqual(
            data_source_transactions[0]["receiver_kind"],
            "data_source",
        )


if __name__ == "__main__":
    unittest.main()
