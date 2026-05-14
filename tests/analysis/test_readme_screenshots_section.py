import os
import unittest


class ReadmeScreenshotsSectionTest(unittest.TestCase):
    def test_readme_has_screenshots_assets_entry(self):
        p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "README.md"))
        txt = open(p, "r", encoding="utf-8").read()
        self.assertTrue("Screenshots / Demo Assets" in txt or "docs/assets/ASSET_INDEX.md" in txt)


if __name__ == "__main__":
    unittest.main()
