import os
import unittest


class ReviewDemoDocsScreenshotsTest(unittest.TestCase):
    def test_review_demo_screenshot_docs_reference_canonical_source(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        with open(os.path.join(root, "docs", "assets", "screenshots", "CAPTURE_PLAN.md"), "r", encoding="utf-8") as f:
            capture_plan = f.read()
        self.assertIn(".reposense_review_demo/current", capture_plan)

        with open(os.path.join(root, "docs", "assets", "screenshots", "MANUAL_CAPTURE_CHECKLIST.md"), "r", encoding="utf-8") as f:
            checklist = f.read()
        self.assertIn(".reposense_review_demo/current", checklist)

        with open(os.path.join(root, "docs", "review", "REPOSITORY_REVIEW_MODE.md"), "r", encoding="utf-8") as f:
            review_doc = f.read()
        self.assertIn("tools/review_demo.ps1", review_doc)
        self.assertIn("Demo and screenshots", review_doc)

        with open(os.path.join(root, "docs", "studio", "STUDIO_UI.md"), "r", encoding="utf-8") as f:
            studio_doc = f.read()
        self.assertIn("studio-review-panel.png", studio_doc)


if __name__ == "__main__":
    unittest.main()
