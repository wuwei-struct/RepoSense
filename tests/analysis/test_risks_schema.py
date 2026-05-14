import unittest

from reposense.analysis.ai.risks_schema import make_report_id, normalize_risks_report


class RisksSchemaTest(unittest.TestCase):
    def test_report_id_stable(self):
        a = make_report_id("r1", with_drilldown=True)
        b = make_report_id("r1", with_drilldown=True)
        self.assertEqual(a, b)

    def test_normalize(self):
        obj = normalize_risks_report(
            {
                "report_id": "rk-1",
                "run_dir": "r",
                "mode": "facts_only",
                "summary": {"total_risks": 1},
                "risk_items": [{"risk_id": "x", "title": "t", "severity": "high", "status": "confirmed"}],
            }
        )
        self.assertEqual(obj["report_id"], "rk-1")
        self.assertEqual(len(obj["risk_items"]), 1)

