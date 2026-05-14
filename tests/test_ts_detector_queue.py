import unittest
from reposense.parsers.typescript_minimal import detect_ts_queue_dispatch, detect_ts_queue_consume


class TsDetectorQueueTest(unittest.TestCase):
    def test_add_maps_to_dispatch(self):
        lines = ['await emailQueue.add("sendWelcome", payload)']
        hits = detect_ts_queue_dispatch(lines)
        self.assertTrue(len(hits) >= 1)
        self.assertEqual(hits[0]["job_name"], "sendWelcome")

    def test_worker_and_process_map_to_consume(self):
        lines = ['new Worker("email", async (job) => {})', "emailQueue.process(async (job) => {})"]
        hits = detect_ts_queue_consume(lines)
        styles = sorted([h["consumer_style"] for h in hits])
        self.assertIn("worker", styles)
        self.assertIn("process", styles)

    def test_non_queue_add_not_reported(self):
        lines = ['arr.add("x")', 'service.add("x")']
        hits = detect_ts_queue_dispatch(lines)
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
