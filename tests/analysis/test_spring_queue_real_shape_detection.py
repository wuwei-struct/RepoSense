import unittest
from pathlib import Path

from reposense.parsers.java_minimal import detect_java_queue_events


FIXTURE = Path(
    "tests/fixtures/repos/queue_cache_real_shapes_min/src/QueueWorker.java"
)


class SpringQueueRealShapeDetectionTest(unittest.TestCase):
    def test_kafka_rabbit_constants_and_dynamic_expression(self):
        lines = FIXTURE.read_text(encoding="utf-8").splitlines()
        events = detect_java_queue_events(lines)["events"]
        self.assertTrue(
            any(
                item.get("queue_system") == "kafka"
                and item.get("topic_name") == "orders"
                and item.get("queue_name_resolved")
                for item in events
            )
        )
        self.assertTrue(
            any(
                item.get("queue_system") == "rabbitmq"
                and item.get("queue_name") == "jobs"
                and item.get("queue_name_resolved")
                for item in events
            )
        )
        self.assertTrue(
            any(
                item.get("queue_name_expr") == "resolveTopic()"
                and not item.get("queue_name_resolved")
                for item in events
            )
        )


if __name__ == "__main__":
    unittest.main()
