import unittest

from tests.analysis.test_queue_reliability_schema import correlation


class KafkaRetryExtractionTest(unittest.TestCase):
    def test_retryable_topic_attempts_and_backoff(self):
        guarded = correlation("spring_kafka", "kafka-guarded")
        unsafe = correlation("spring_kafka", "kafka-unsafe")
        self.assertEqual(guarded["retry_status"], "explicit_retry")
        self.assertEqual(guarded["retry_policy"]["attempts"], 3)
        self.assertEqual(unsafe["retry_policy"]["attempts"], 4)
        self.assertTrue(
            any(
                ref.get("rule_id") == "kafka_retry_configuration"
                for ref in guarded["evidence_refs"]
            )
        )
        retry_refs = [
            ref
            for ref in unsafe["evidence_refs"]
            if ref.get("rule_id") == "kafka_retry_configuration"
        ]
        self.assertEqual(retry_refs[0]["start_line"], 32)


if __name__ == "__main__":
    unittest.main()
