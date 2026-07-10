import os
import re
import unittest


REVIEW_SCREENSHOTS = [
    "repository-review-report.png",
    "human-review-required.png",
    "studio-review-panel.png",
    "code-health-summary.png",
    "permission-risk-report.png",
    "authz-matrix-report.png",
    "context-pack-review-section.png",
]


class ReviewDemoScreenshotAssetsTest(unittest.TestCase):
    def test_review_screenshot_assets_are_indexed_with_truthful_status(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        index_path = os.path.join(root, "docs", "assets", "ASSET_INDEX.md")
        with open(index_path, "r", encoding="utf-8") as f:
            text = f.read()

        self.assertIn(".reposense_review_demo/current", text)
        for name in REVIEW_SCREENSHOTS:
            self.assertIn(name, text)
            pattern = re.compile(r"\|\s*[^|]*\|\s*`docs/assets/screenshots/" + re.escape(name) + r"`\s*\|[^|]*\|\s*([^|]+?)\s*\|")
            match = pattern.search(text)
            self.assertIsNotNone(match, name)
            status = match.group(1).strip()
            png_path = os.path.join(root, "docs", "assets", "screenshots", name)
            if status == "captured":
                self.assertTrue(os.path.isfile(png_path), name)
            if not os.path.isfile(png_path):
                self.assertNotEqual(status, "captured", name)


if __name__ == "__main__":
    unittest.main()
