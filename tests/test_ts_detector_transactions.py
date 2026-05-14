import unittest
from reposense.parsers.typescript_minimal import detect_ts_prisma_transactions, detect_ts_typeorm_transactions


class TsDetectorTransactionsTest(unittest.TestCase):
    def test_prisma_transaction_detected(self):
        lines = [
            "await prisma.$transaction(async (tx) => {",
            "await tx.user.create({})",
            "})",
        ]
        hits = detect_ts_prisma_transactions(lines)
        self.assertTrue(len(hits) >= 1)
        self.assertEqual(hits[0]["framework"], "prisma")

    def test_typeorm_transaction_detected(self):
        lines = [
            "await dataSource.transaction(async (manager) => {",
            "await manager.save(user)",
            "})",
        ]
        hits = detect_ts_typeorm_transactions(lines)
        self.assertTrue(len(hits) >= 1)
        self.assertEqual(hits[0]["framework"], "typeorm")

    def test_non_transaction_name_not_reported(self):
        lines = ["const transaction = () => {}", "doTransaction()"]
        self.assertEqual(detect_ts_prisma_transactions(lines), [])
        self.assertEqual(detect_ts_typeorm_transactions(lines), [])


if __name__ == "__main__":
    unittest.main()
