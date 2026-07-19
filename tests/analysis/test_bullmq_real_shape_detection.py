import unittest
from pathlib import Path

from reposense.parsers.typescript_minimal import (
    detect_ts_queue_consume,
    detect_ts_queue_dispatch,
)


FIXTURE = Path("tests/fixtures/repos/queue_cache_real_shapes_min/src/queue.ts")


class BullMqRealShapeDetectionTest(unittest.TestCase):
    def test_alias_static_and_dynamic_queue_names(self):
        lines = FIXTURE.read_text(encoding="utf-8").splitlines()
        dispatch = detect_ts_queue_dispatch(lines)
        consume = detect_ts_queue_consume(lines)
        self.assertTrue(
            any(
                item["queue_name"] == "email"
                and item["queue_name_resolved"]
                for item in dispatch
            )
        )
        self.assertTrue(
            any(
                item["queue_name"] == "email"
                and item["queue_name_resolved"]
                for item in consume
            )
        )
        dynamic = [
            item
            for item in dispatch + consume
            if item.get("queue_name_expr") == "dynamicQueueName"
        ]
        self.assertTrue(dynamic)
        self.assertTrue(
            all(not item["queue_name_resolved"] for item in dynamic)
        )

    def test_nest_injected_queue_and_processor(self):
        lines = [
            "import { InjectQueue, Processor, WorkerHost } from '@nestjs/bullmq';",
            "@Processor('notifications')",
            "class NotificationsProcessor extends WorkerHost {}",
            "class Scheduler {",
            "  constructor(@InjectQueue('notifications') private readonly queue: Queue) {}",
            "  async send() { await this.queue.add('welcome', {}); }",
            "}",
        ]
        dispatch = detect_ts_queue_dispatch(lines)
        consume = detect_ts_queue_consume(lines)
        self.assertTrue(
            any(item["queue_name"] == "notifications" for item in dispatch)
        )
        self.assertTrue(
            any(
                item["queue_name"] == "notifications"
                and item["consumer_style"] == "nest_processor"
                for item in consume
            )
        )


if __name__ == "__main__":
    unittest.main()
