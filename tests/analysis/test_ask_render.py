import unittest

from reposense.analysis.ai.ask_render import render_ask_markdown


class AskRenderTest(unittest.TestCase):
    def test_markdown_sections(self):
        md = render_ask_markdown(
            {
                "question": "q",
                "question_type": "summary",
                "mode": "facts_only",
                "confirmed": [{"claim": "c", "because": "b"}],
                "inferred": [{"claim": "i", "why_not_confirmed": "w"}],
                "unknown": [{"question": "u", "suggested_next_step": "n"}],
                "evidence_index": [],
                "limitations": ["l"],
            }
        )
        self.assertIn("用户问题", md)
        self.assertIn("问题分类", md)
        self.assertIn("已证实", md)
        self.assertIn("合理推测", md)
        self.assertIn("未知", md)

