import unittest

from reposense.analysis.ai.explain_render import render_explain_markdown


class ExplainRenderTest(unittest.TestCase):
    def test_markdown_sections(self):
        md = render_explain_markdown(
            {
                "target_type": "pattern",
                "target_id": "p1",
                "mode": "facts_only",
                "confirmed": [{"claim": "c1", "because": "b1", "confidence": 0.9, "evidence_refs": []}],
                "inferred": [{"claim": "i1", "signals": ["s1"], "why_not_confirmed": "w1"}],
                "unknown": [{"question": "q1", "missing_evidence": ["m1"], "suggested_next_step": "n1"}],
                "evidence_index": [],
                "limitations": ["l1"],
            }
        )
        self.assertIn("已证实", md)
        self.assertIn("合理推测", md)
        self.assertIn("未知", md)
        self.assertIn("已知局限", md)

