import shutil
import unittest

from reposense.analysis.ai.summary_engine import generate_facts_only_summary
from tests.analysis._ai_summary_fixture import build_ai_summary_run_dir


class AISummaryEngineTest(unittest.TestCase):
    def test_summary_counts_and_actions_stable(self):
        rd = build_ai_summary_run_dir()
        try:
            s1 = generate_facts_only_summary(rd)
            s2 = generate_facts_only_summary(rd)
            self.assertEqual(s1["risk_summary"]["total_patterns"], 2)
            self.assertTrue(len(s1["priority_actions"]) >= 1)
            self.assertEqual(
                [x["action_id"] for x in s1["priority_actions"]],
                [x["action_id"] for x in s2["priority_actions"]],
            )
            self.assertEqual(s1["generated_at"], "1234567890")
        finally:
            shutil.rmtree(rd, ignore_errors=True)

