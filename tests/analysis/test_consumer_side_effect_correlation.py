import unittest

from tests.analysis.test_queue_reliability_schema import correlation


class ConsumerSideEffectCorrelationTest(unittest.TestCase):
    def test_same_handler_effects_only(self):
        unsafe = correlation("bullmq", "bull-unsafe")
        passive = correlation("bullmq", "bull-passive")
        self.assertEqual(
            {item["kind"] for item in unsafe["consumer_side_effects"]},
            {"db.write"},
        )
        self.assertEqual(passive["consumer_side_effects"], [])
        self.assertEqual(
            passive["coverage_status"], "insufficient_evidence"
        )


if __name__ == "__main__":
    unittest.main()
