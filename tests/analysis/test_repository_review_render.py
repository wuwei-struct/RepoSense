import unittest

from reposense.analysis.review.review_render import render_repository_review_markdown


class RepositoryReviewRenderTest(unittest.TestCase):
    def test_markdown_contains_core_sections(self):
        md = render_repository_review_markdown(
            {
                "review_summary": {"decision": "WARN", "total_risks": 1, "human_review_required_count": 1},
                "backend_risk_review": {"top_risks": []},
                "human_review_required": [
                    {
                        "path": "svc/order.py",
                        "reason": ["DB write found"],
                        "required_decision": ["Should this operation be transactional?"],
                    }
                ],
                "limitations": ["Does not replace human code review."],
            }
        )
        self.assertIn("Review Summary", md)
        self.assertIn("Human Review Required", md)
        self.assertIn("Limitations", md)


if __name__ == "__main__":
    unittest.main()

