import json
import tempfile
import unittest
from pathlib import Path

from reposense.analysis.review.review_engine import generate_repository_review
from reposense.context_pack import build_context_pack
from reposense.run_manifest import build_run_manifest
from tools.validation.queue_cache_validation import write_validation


class QueueCacheValidationArtifactsTest(unittest.TestCase):
    def test_manifest_context_pack_and_review_include_validation(self):
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
                "dispatch();\n", encoding="utf-8"
            )
            (evidence / "E1.json").write_text(
                json.dumps(
                    {
                        "path": str((repo / "queue.ts").resolve()),
                        "start_line": 1,
                        "end_line": 1,
                        "snippet": "dispatch();",
                    }
                ),
                encoding="utf-8",
            )
            (run / "event_graph.json").write_text(
                json.dumps(
                    {
                        "nodes": [
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
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (run / "report.json").write_text(
                '{"run_summary":{},"findings":[]}', encoding="utf-8"
            )
            (run / "coverage.json").write_text("{}", encoding="utf-8")
            write_validation(run, repo)
            review = generate_repository_review(str(run))
            self.assertEqual(
                review["queue_cache_review"]["validation_status"],
                "enabled",
            )
            build_context_pack(str(run))
            manifest = build_run_manifest(str(run), write=False)
            paths = {item["path"] for item in manifest["artifacts"]}
            self.assertIn("queue_cache_validation.json", paths)
            self.assertIn(
                "context_pack/ARTIFACTS/queue_cache_validation.json",
                paths,
            )
            index = json.loads(
                (run / "context_pack/MAP/index.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIn(
                "queue_cache_validation",
                index["outputs"],
            )


if __name__ == "__main__":
    unittest.main()
