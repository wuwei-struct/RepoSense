import unittest
from pathlib import Path

from reposense.parsers.typescript_minimal import detect_ts_cache_ops


FIXTURE = Path("tests/fixtures/repos/queue_cache_real_shapes_min/src/cache.ts")


class IoredisRealShapeDetectionTest(unittest.TestCase):
    def test_client_and_pipeline_operations(self):
        lines = FIXTURE.read_text(encoding="utf-8").splitlines()
        hits = detect_ts_cache_ops(lines)
        operations = {item["cache_op"] for item in hits}
        self.assertTrue(
            {"get", "setex", "del", "hget", "hset", "hdel"}.issubset(
                operations
            )
        )
        self.assertTrue(
            all(item["framework"] == "ioredis" for item in hits)
        )


if __name__ == "__main__":
    unittest.main()
