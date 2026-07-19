import unittest

from tests.analysis._typeorm_fixture import false_positive_operations


class TypeOrmReceiverFalsePositiveGuardsTest(unittest.TestCase):
    def test_ordinary_redis_http_map_and_name_only_receivers_are_ignored(self):
        self.assertEqual(false_positive_operations(), [])


if __name__ == "__main__":
    unittest.main()
