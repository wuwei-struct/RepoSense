import os
import re
import unittest


SCREENSHOTS = [
    "repository-review-report.png",
    "human-review-required.png",
    "studio-review-panel.png",
    "code-health-summary.png",
    "permission-risk-report.png",
    "authz-matrix-report.png",
    "context-pack-review-section.png",
]


class ReviewScreenshotAssetsPresentTest(unittest.TestCase):
    def test_captured_review_screenshots_are_valid_png_files(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        index_path = os.path.join(root, "docs", "assets", "ASSET_INDEX.md")
        with open(index_path, "r", encoding="utf-8") as handle:
            index = handle.read()

        for name in SCREENSHOTS:
            path = os.path.join(root, "docs", "assets", "screenshots", name)
            self.assertTrue(os.path.isfile(path), name)
            self.assertLess(os.path.getsize(path), 2 * 1024 * 1024, name)
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(8), b"\x89PNG\r\n\x1a\n", name)

            row = re.search(
                r"\|\s*[^|]+\|\s*`docs/assets/screenshots/"
                + re.escape(name)
                + r"`\s*\|[^|]+\|\s*captured\s*\|",
                index,
            )
            self.assertIsNotNone(row, name)


if __name__ == "__main__":
    unittest.main()
