import os
import unittest


class ReadmeStudioReviewScreenshotTest(unittest.TestCase):
    def test_readmes_embed_the_captured_studio_review_panel(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        relative_path = "docs/assets/screenshots/studio-review-panel.png"
        self.assertTrue(os.path.isfile(os.path.join(root, relative_path)))

        for name in ["README.md", "README.zh-CN.md"]:
            with open(os.path.join(root, name), "r", encoding="utf-8") as handle:
                text = handle.read()
            self.assertIn("Review Artifact Cards", text)
            self.assertIn(f"]({relative_path})", text)
            self.assertNotIn("pending_manual_capture", text)


if __name__ == "__main__":
    unittest.main()
