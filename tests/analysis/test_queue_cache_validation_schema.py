import tempfile
import unittest
from pathlib import Path

from tools.validation.queue_cache_validation import (
    MATCH_STATUSES,
    build_validation,
)


class QueueCacheValidationSchemaTest(unittest.TestCase):
    def test_output_has_stable_schema_and_statuses(self):
        with tempfile.TemporaryDirectory(
            dir=".tmp_test_runs/temp"
        ) as root:
            run_dir = Path(root) / "run"
            repo_dir = Path(root) / "repo"
            run_dir.mkdir()
            repo_dir.mkdir()
            (run_dir / "event_graph.json").write_text(
                '{"nodes":[]}', encoding="utf-8"
            )
            result = build_validation(run_dir, repo_dir)
        self.assertEqual(result["version"], "queue_cache_validation_v1")
        self.assertIn("summary", result)
        self.assertTrue(
            all(
                item["match_status"] in MATCH_STATUSES
                for item in result["queue_observations"]
            )
        )


if __name__ == "__main__":
    unittest.main()
