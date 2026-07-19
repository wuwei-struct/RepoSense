import json
import tempfile
import unittest
from pathlib import Path

from tools.validation.queue_cache_validation import build_validation
from tools.validation.real_repo_smoke import _event_counts


class QueueCacheValidationSummaryTest(unittest.TestCase):
    def test_summary_uses_event_graph_and_valid_evidence(self):
        with tempfile.TemporaryDirectory(
            dir=".tmp_test_runs/temp"
        ) as root:
            root_path = Path(root)
            repo = root_path / "repo"
            run = root_path / "run"
            evidence = run / "evidence"
            repo.mkdir()
            evidence.mkdir(parents=True)
            (repo / "queue.ts").write_text(
                "dispatch();\nconsume();\n", encoding="utf-8"
            )
            for eid, line in (("E1", 1), ("E2", 2)):
                (evidence / f"{eid}.json").write_text(
                    json.dumps(
                        {
                            "path": str((repo / "queue.ts").resolve()),
                            "start_line": line,
                            "end_line": line,
                            "snippet": "dispatch();" if line == 1 else "consume();",
                        }
                    ),
                    encoding="utf-8",
                )
            nodes = [
                {
                    "event_id": "d1",
                    "type": "queue_dispatch",
                    "confidence": 0.8,
                    "evidence": ["E1"],
                    "meta": {
                        "framework": "bullmq",
                        "queue_name": "jobs",
                        "queue_name_resolved": True,
                    },
                },
                {
                    "event_id": "c1",
                    "type": "queue_consume",
                    "confidence": 0.8,
                    "evidence": ["E2"],
                    "meta": {
                        "framework": "bullmq",
                        "queue_name": "jobs",
                        "queue_name_resolved": True,
                    },
                },
            ]
            (run / "event_graph.json").write_text(
                json.dumps({"nodes": nodes}), encoding="utf-8"
            )
            result = build_validation(run, repo, case_id="fixture")
        summary = result["summary"]
        self.assertEqual(summary["matched_producer_consumer_pairs"], 1)
        self.assertEqual(summary["evidence_errors"], 0)
        self.assertEqual(summary["evidence_valid"], 2)

    def test_real_repo_summary_maps_cache_op_metadata(self):
        counts = _event_counts(
            {
                "nodes": [
                    {
                        "type": "cache_op",
                        "meta": {"cache.kind": "cache.write"},
                    }
                ]
            }
        )
        self.assertEqual(counts["cache.write"], 1)


if __name__ == "__main__":
    unittest.main()
