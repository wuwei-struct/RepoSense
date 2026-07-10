import os
import unittest


class ReviewDemoDocsTest(unittest.TestCase):
    def test_review_demo_docs_and_assets_are_indexed(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        with open(os.path.join(root, "docs", "assets", "ASSET_INDEX.md"), "r", encoding="utf-8") as f:
            asset_index = f.read()
        self.assertIn(".reposense_review_demo/current", asset_index)
        self.assertIn("repository-review-report.png", asset_index)
        self.assertIn("studio-review-panel.png", asset_index)

        with open(os.path.join(root, "docs", "assets", "screenshots", "CAPTURE_PLAN.md"), "r", encoding="utf-8") as f:
            capture_plan = f.read()
        self.assertIn("repository-review-report", capture_plan)
        self.assertIn(".reposense_review_demo/current", capture_plan)

        with open(os.path.join(root, "README.md"), "r", encoding="utf-8") as f:
            readme = f.read()
        with open(os.path.join(root, "docs", "review", "REPOSITORY_REVIEW_MODE.md"), "r", encoding="utf-8") as f:
            review_doc = f.read()
        self.assertTrue("tools/review_demo.ps1" in readme or "tools/review_demo.ps1" in review_doc)


if __name__ == "__main__":
    unittest.main()
