import unittest

from tests.analysis.test_queue_reliability_schema import correlation


class RabbitRetryExtractionTest(unittest.TestCase):
    def test_retryable_and_setnx_guard(self):
        guarded = correlation("spring_rabbit", "rabbit-guarded")
        unsafe = correlation("spring_rabbit", "rabbit-unsafe")
        self.assertEqual(guarded["retry_status"], "explicit_retry")
        self.assertEqual(
            guarded["consumer_idempotency_status"],
            "redis_atomic_guard_observed",
        )
        self.assertEqual(
            unsafe["coverage_status"], "retry_without_consumer_guard"
        )


if __name__ == "__main__":
    unittest.main()
