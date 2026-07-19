import unittest

from reposense.analysis.messaging.idempotency_extractor import _find_guard


class ConsumerIdempotencyGuardDetectionTest(unittest.TestCase):
    def test_check_then_write_is_not_strong_guard(self):
        lines = [
            "void consume(String messageId) {",
            "  if (events.exists(messageId)) return;",
            "  events.save(messageId);",
            "}",
        ]
        status, refs, limitations = _find_guard(
            "src/Consumer.java", lines, [(1, 4)]
        )
        self.assertEqual(status, "guard_signal_observed")
        self.assertTrue(refs)
        self.assertIn(
            "check_then_write_atomicity_unresolved", limitations
        )

    def test_plain_message_id_logging_is_not_a_guard(self):
        lines = [
            "void consume(String messageId) {",
            "  log.info(messageId);",
            "}",
        ]
        status, _, _ = _find_guard("src/Consumer.java", lines, [(1, 3)])
        self.assertEqual(status, "none_observed")


if __name__ == "__main__":
    unittest.main()
