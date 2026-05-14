import unittest

from reposense.analysis.ai.ask_classifier import classify_question


class AskClassifierTest(unittest.TestCase):
    def test_four_types(self):
        self.assertEqual(classify_question("这个系统主要做什么"), "summary")
        self.assertEqual(classify_question("有哪些风险"), "risk")
        self.assertEqual(classify_question("证据是什么"), "evidence")
        self.assertEqual(classify_question("流程怎么走"), "flow")

    def test_unsupported(self):
        self.assertEqual(classify_question("请重构整个项目"), "unsupported")

