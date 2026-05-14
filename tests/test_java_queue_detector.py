import unittest
from reposense.parsers.java_minimal import detect_java_queue_events


class JavaQueueDetectorTest(unittest.TestCase):
    def test_kafka_listener_and_dispatch(self):
        lines = [
            "class K {",
            "  private KafkaTemplate<String,String> kafkaTemplate;",
            '  @KafkaListener(topics="orders")',
            "  public void onMsg(String p) {}",
            '  public void send(String p){ kafkaTemplate.send("orders", p); }',
            "}",
        ]
        out = detect_java_queue_events(lines)
        ev = out.get("events") or []
        self.assertTrue(any(x.get("event_kind") == "queue.consume" and x.get("queue_system") == "kafka" for x in ev))
        self.assertTrue(any(x.get("event_kind") == "queue.dispatch" and x.get("queue_system") == "kafka" for x in ev))

    def test_rabbit_listener_and_dispatch(self):
        lines = [
            "class R {",
            "  private RabbitTemplate rabbitTemplate;",
            '  @RabbitListener(queues="jobs")',
            "  public void onMsg(String p) {}",
            '  public void send(String p){ rabbitTemplate.convertAndSend("jobs", p); }',
            "}",
        ]
        out = detect_java_queue_events(lines)
        ev = out.get("events") or []
        self.assertTrue(any(x.get("event_kind") == "queue.consume" and x.get("queue_system") == "rabbitmq" for x in ev))
        self.assertTrue(any(x.get("event_kind") == "queue.dispatch" and x.get("queue_system") == "rabbitmq" for x in ev))

    def test_no_false_positive(self):
        lines = [
            "class X {",
            "  public void send(String p) { sender.send(p); }",
            "  public void convert(String p) { obj.convertAndSend(p); }",
            "}",
        ]
        out = detect_java_queue_events(lines)
        self.assertEqual(out.get("events") or [], [])


if __name__ == "__main__":
    unittest.main()
