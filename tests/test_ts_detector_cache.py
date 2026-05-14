import unittest
from reposense.parsers.typescript_minimal import detect_ts_cache_ops


class TsDetectorCacheTest(unittest.TestCase):
    def test_get_set_del(self):
        lines = ['await client.get("k1")', 'await client.set("k1", "v")', 'await client.del("k1")']
        hits = detect_ts_cache_ops(lines)
        kinds = sorted([h["event_kind"] for h in hits])
        self.assertIn("cache.read", kinds)
        self.assertIn("cache.write", kinds)
        self.assertIn("cache.invalidate", kinds)

    def test_normal_get_set_not_reported(self):
        lines = ['obj.get("k")', 'obj.set("k","v")']
        hits = detect_ts_cache_ops(lines)
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
