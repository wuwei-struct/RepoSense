import unittest
from reposense.events.taxonomy import is_valid_event_kind, event_family, normalize_language, normalize_framework, normalize_event_kind


class EventTaxonomyTest(unittest.TestCase):
    def test_kind_and_family(self):
        self.assertTrue(is_valid_event_kind("api.route"))
        self.assertEqual(event_family("api.route"), "api")
        self.assertEqual(event_family("db.transaction"), "db")
        self.assertEqual(event_family("unknown.kind"), "unknown")

    def test_unknown_safe(self):
        self.assertEqual(normalize_language("xlang"), "unknown")
        self.assertEqual(normalize_framework("xframework"), "unknown")
        self.assertIsNone(normalize_event_kind("not_exists", {}))

    def test_kind_mapping(self):
        self.assertEqual(normalize_event_kind("api", {}), "api.route")
        self.assertEqual(normalize_event_kind("tx_boundary", {}), "db.transaction")
        self.assertEqual(normalize_event_kind("queue_dispatch", {}), "queue.dispatch")
        self.assertEqual(normalize_event_kind("cache_op", {"cache.op": "get"}), "cache.read")
        self.assertEqual(normalize_event_kind("cache_op", {"cache.op": "set"}), "cache.write")
        self.assertEqual(normalize_event_kind("cache_op", {"cache.op": "del"}), "cache.invalidate")


if __name__ == "__main__":
    unittest.main()
