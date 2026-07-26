import unittest

from tests.analysis.test_queue_reliability_schema import correlation


class BullMqIdempotencyCorrelationTest(unittest.TestCase):
    def test_consumer_guard_and_producer_identity_are_distinct(self):
        guarded = correlation("bullmq", "bull-guarded")
        producer_only = correlation("bullmq", "bull-producer-only")
        unsafe = correlation("bullmq", "bull-unsafe")
        self.assertEqual(
            guarded["consumer_idempotency_status"],
            "redis_atomic_guard_observed",
        )
        self.assertEqual(
            guarded["coverage_status"], "retry_with_consumer_guard"
        )
        self.assertEqual(
            producer_only["producer_identity_status"], "stable_job_id"
        )
        self.assertEqual(
            producer_only["coverage_status"],
            "retry_with_producer_dedupe_only",
        )
        self.assertEqual(
            unsafe["coverage_status"], "retry_without_consumer_guard"
        )


if __name__ == "__main__":
    unittest.main()
