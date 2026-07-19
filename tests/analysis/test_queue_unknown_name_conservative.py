import unittest

from reposense.analysis.ai.pattern_rules import run_all_rules
from tools.validation.queue_cache_validation import _match_queues


class QueueUnknownNameConservativeTest(unittest.TestCase):
    def test_unknown_name_is_not_confirmed_orphan(self):
        observations = [
            {
                "event_id": "d1",
                "operation": "queue.dispatch",
                "framework": "bullmq",
                "queue_name": "",
                "queue_name_resolved": False,
                "match_status": "unknown_name",
            }
        ]
        self.assertEqual(_match_queues(observations), [])
        self.assertEqual(observations[0]["match_status"], "unknown_name")

        patterns = run_all_rules(
            {
                "findings": [],
                "cross_language_summary": {},
                "cross_language_links": {},
                "events": [
                    {
                        "event_id": "d1",
                        "type": "queue_dispatch",
                        "confidence": 0.8,
                        "meta": {
                            "path": "src/queue.ts",
                            "start_line": 3,
                            "end_line": 3,
                            "framework": "bullmq",
                            "queue.task": "welcome",
                            "queue_name_resolved": False,
                        },
                    }
                ],
            }
        )
        orphan = next(
            item
            for item in patterns
            if item["pattern_type"] == "queue_without_consumer"
        )
        self.assertEqual(orphan["status"], "suspected")
        self.assertIn(
            "queue_name_unresolved",
            orphan["metadata"]["limitations"],
        )


if __name__ == "__main__":
    unittest.main()
