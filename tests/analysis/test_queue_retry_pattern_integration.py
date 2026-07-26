import unittest

from tests.analysis.test_queue_reliability_schema import load_artifact


class QueueRetryPatternIntegrationTest(unittest.TestCase):
    def test_patterns_are_suspected_and_evidence_backed(self):
        patterns = [
            item
            for item in load_artifact("patterns.json")["patterns"]
            if item["pattern_type"]
            in {
                "queue_retry_without_idempotency_guard",
                "queue_consumer_side_effect_without_idempotency_evidence",
            }
        ]
        self.assertEqual(len(patterns), 5)
        self.assertTrue(all(item["status"] == "suspected" for item in patterns))
        self.assertTrue(all(item["evidence_refs"] for item in patterns))
        self.assertFalse(
            any("bull-guarded" in item.get("title", "") for item in patterns)
        )


if __name__ == "__main__":
    unittest.main()
