import unittest

from tests.analysis.test_queue_reliability_schema import correlation


class KafkaTransportVsBusinessIdempotencyTest(unittest.TestCase):
    def test_transport_idempotence_does_not_satisfy_consumer_guard(self):
        guarded = correlation("spring_kafka", "kafka-guarded")
        unsafe = correlation("spring_kafka", "kafka-unsafe")
        self.assertEqual(
            guarded["consumer_idempotency_status"],
            "inbox_or_processed_event_observed",
        )
        self.assertEqual(
            guarded["coverage_status"], "retry_with_consumer_guard"
        )
        self.assertEqual(
            unsafe["producer_identity_status"],
            "transport_idempotence_observed",
        )
        self.assertTrue(
            any(
                ref.get("rule_id") == "kafka_transport_idempotence"
                for ref in unsafe["evidence_refs"]
            )
        )
        self.assertEqual(
            unsafe["coverage_status"], "retry_with_producer_dedupe_only"
        )


if __name__ == "__main__":
    unittest.main()
