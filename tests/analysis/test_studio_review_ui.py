import os
import unittest


class StudioReviewUiTest(unittest.TestCase):
    def test_index_contains_review_panel_markers(self):
        root = os.path.join(os.getcwd(), "webui", "studio")
        with open(os.path.join(root, "index.html"), "r", encoding="utf-8") as f:
            html = f.read()
        with open(os.path.join(root, "artifact-cards.js"), "r", encoding="utf-8") as f:
            html += f.read()
        with open(os.path.join(os.getcwd(), "reposense", "studio", "artifact_catalog.py"), "r", encoding="utf-8") as f:
            html += f.read()
        for marker in [
            "Repository Review",
            "Human Review Required",
            "Code Health",
            "Permission Review",
            "AuthZ Matrix",
            "Context Pack REVIEW",
            "human_review_required.md",
            "authz_negative_test_plan.md",
            "No primary review artifact was generated for this run.",
        ]:
            self.assertIn(marker, html)


if __name__ == "__main__":
    unittest.main()
