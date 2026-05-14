import shutil
import unittest

from reposense.analysis.ai.ask_engine import generate_ask_answer
from tests.analysis._drilldown_fixture import build_drilldown_run_dir


class AskEngineTest(unittest.TestCase):
    def test_summary_and_unsupported(self):
        rd = build_drilldown_run_dir()
        try:
            a = generate_ask_answer(rd, "这个系统主要做什么？")
            self.assertEqual(a.get("question_type"), "summary")
            u = generate_ask_answer(rd, "请重构整个项目")
            self.assertEqual(u.get("question_type"), "unsupported")
            self.assertTrue(len(u.get("unknown") or []) >= 1)
        finally:
            shutil.rmtree(rd, ignore_errors=True)

    def test_evidence_with_drilldown(self):
        rd = build_drilldown_run_dir()
        try:
            a = generate_ask_answer(rd, "证据是什么？", with_drilldown=True)
            self.assertEqual(a.get("question_type"), "evidence")
            self.assertIn(a.get("mode"), ("facts_only", "facts_plus_drilldown"))
        finally:
            shutil.rmtree(rd, ignore_errors=True)

