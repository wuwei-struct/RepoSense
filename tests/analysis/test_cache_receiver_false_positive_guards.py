import unittest
from pathlib import Path

from reposense.parsers.typescript_minimal import detect_ts_cache_ops


FIXTURE = Path("tests/fixtures/repos/queue_cache_real_shapes_min/src/cache.ts")


class CacheReceiverFalsePositiveGuardsTest(unittest.TestCase):
    def test_map_http_and_repository_calls_are_not_redis(self):
        lines = FIXTURE.read_text(encoding="utf-8").splitlines()
        hits = detect_ts_cache_ops(lines)
        callees = {item["callee_expr"] for item in hits}
        self.assertNotIn("map.get", callees)
        self.assertNotIn("map.set", callees)
        self.assertNotIn("httpClient.delete", callees)
        self.assertNotIn("repository.delete", callees)
        self.assertEqual(
            detect_ts_cache_ops(
                ["const redisStatus = gauge;", "redisStatus.set(1);"]
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
