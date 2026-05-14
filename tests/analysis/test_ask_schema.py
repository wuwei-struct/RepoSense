import unittest

from reposense.analysis.ai.ask_schema import build_ask_request, normalize_answer


class AskSchemaTest(unittest.TestCase):
    def test_request_stable(self):
        a = build_ask_request("r", "q1", with_drilldown=True)
        b = build_ask_request("r", "q1", with_drilldown=True)
        self.assertEqual(a["request_id"], b["request_id"])

    def test_answer_normalize(self):
        x = normalize_answer({"request_id": "ask-1", "question_type": "summary", "confirmed": [{}]})
        self.assertEqual(x["request_id"], "ask-1")
        self.assertEqual(x["question_type"], "summary")
        self.assertEqual(len(x["confirmed"]), 1)

