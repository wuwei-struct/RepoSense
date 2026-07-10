import os
import unittest


class StudioReviewUiTest(unittest.TestCase):
    def test_index_contains_review_panel_markers(self):
        path = os.path.join(os.getcwd(), "webui", "studio", "index.html")
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        for marker in [
            "Repository Review",
            "Human Review Required",
            "Code Health",
            "Permission Review",
            "AuthZ Matrix",
            "Context Pack REVIEW",
            "human_review_required.md",
            "authz_negative_test_plan.md",
            "Repository Review artifacts are not generated yet.",
        ]:
            self.assertIn(marker, html)


if __name__ == "__main__":
    unittest.main()
