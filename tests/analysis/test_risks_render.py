import unittest

from reposense.analysis.ai.risks_render import render_risks_markdown


class RisksRenderTest(unittest.TestCase):
    def test_markdown_stable(self):
        md = render_risks_markdown(
            {
                "mode": "facts_only",
                "summary": {"total_risks": 1, "gate_status": "warn"},
                "risk_items": [
                    {
                        "title": "T1",
                        "severity": "high",
                        "status": "confirmed",
                        "priority_score": 50,
                        "why_it_matters": "W",
                        "confirmed": [{}],
                        "suspected": [],
                        "unknown": [],
                        "evidence_refs": [{}],
                        "recommended_action": "A",
                    }
                ],
                "priority_actions": [{"title": "A1", "reason": "R"}],
                "evidence_index": [],
                "limitations": ["L1"],
            }
        )
        self.assertIn("Immediate attention", md)
        self.assertIn("Needs review", md)
        self.assertIn("Contextual watchlist", md)

