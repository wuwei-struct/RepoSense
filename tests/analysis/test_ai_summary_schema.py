import unittest

from reposense.analysis.ai.summary_schema import normalize_summary, validate_summary


class AISummarySchemaTest(unittest.TestCase):
    def test_normalize_and_validate(self):
        s = normalize_summary({"run_dir": "x"})
        self.assertEqual(s["mode"], "facts_only")
        self.assertEqual(validate_summary(s), [])

    def test_invalid_mode_rejected(self):
        s = {"mode": "model", "project_overview": {}, "stack_summary": {}, "surface_summary": {}, "flow_summary": {}, "risk_summary": {}, "priority_actions": [], "evidence_index": [], "metadata": {}}
        errs = validate_summary(s)
        self.assertIn("mode must be facts_only", errs)

