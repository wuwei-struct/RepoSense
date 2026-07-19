import unittest

from tools.validation.queue_cache_validation import _match_queues


def _item(event_id, operation, framework, name, resolved=True):
    return {
        "event_id": event_id,
        "operation": operation,
        "framework": framework,
        "queue_name": name,
        "queue_name_resolved": resolved,
        "match_status": "unknown_name",
    }


class QueueProducerConsumerMatchingTest(unittest.TestCase):
    def test_framework_aware_matching(self):
        observations = [
            _item("d1", "queue.dispatch", "bullmq", "jobs"),
            _item("c1", "queue.consume", "bullmq", "jobs"),
            _item("c2", "queue.consume", "spring_kafka", "jobs"),
        ]
        pairs = _match_queues(observations)
        statuses = {
            (item["framework"], item["queue_name"]): item["match_status"]
            for item in pairs
        }
        self.assertEqual(statuses[("bullmq", "jobs")], "matched")
        self.assertEqual(
            statuses[("spring_kafka", "jobs")], "consume_only"
        )


if __name__ == "__main__":
    unittest.main()
