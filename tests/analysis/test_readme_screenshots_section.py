import os
import re
import unittest


class ReadmeScreenshotsSectionTest(unittest.TestCase):
    def test_readme_has_screenshots_assets_entry(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        p = os.path.join(root, "README.md")
        with open(p, "r", encoding="utf-8") as f:
            txt = f.read()
        self.assertIn("docs/assets/ASSET_INDEX.md", txt)
        self.assertIn(".reposense_release_demo/current", txt)

    def test_readme_does_not_embed_missing_png(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        p = os.path.join(root, "README.md")
        with open(p, "r", encoding="utf-8") as f:
            txt = f.read()
        for rel in re.findall(r"!\[[^\]]*\]\(([^)]+\.png)\)", txt):
            self.assertTrue(os.path.isfile(os.path.join(root, rel)), f"README embeds missing PNG: {rel}")


if __name__ == "__main__":
    unittest.main()
