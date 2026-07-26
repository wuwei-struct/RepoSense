import unittest

from tests.analysis.test_queue_reliability_schema import correlation


class BullMqRetryExtractionTest(unittest.TestCase):
    def test_explicit_default_and_dynamic_attempts(self):
        guarded = correlation("bullmq", "bull-guarded")
        producer_only = correlation("bullmq", "bull-producer-only")
        dynamic = correlation("bullmq", "bull-dynamic")
        self.assertEqual(guarded["retry_status"], "explicit_retry")
        self.assertEqual(guarded["retry_policy"]["attempts"], 3)
        retry_refs = [
            ref
            for ref in guarded["evidence_refs"]
            if ref.get("rule_id") == "queue_retry_configuration"
        ]
        self.assertIn("attempts", retry_refs[0]["snippet"])
        self.assertEqual(producer_only["retry_policy"]["source"], "default_job_options")
        self.assertEqual(dynamic["retry_status"], "dynamic_or_unresolved")
        self.assertIn("retry_configuration_dynamic", dynamic["limitations"])


if __name__ == "__main__":
    unittest.main()
