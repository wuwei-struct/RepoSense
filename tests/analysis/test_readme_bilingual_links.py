import os
import unittest


class ReadmeBilingualLinksTest(unittest.TestCase):
    def test_bilingual_files_and_links(self):
        self.assertTrue(os.path.isfile("README.md"))
        self.assertTrue(os.path.isfile("README.zh-CN.md"))

        with open("README.md", "r", encoding="utf-8") as f:
            en = f.read()
        with open("README.zh-CN.md", "r", encoding="utf-8") as f:
            zh = f.read()

        self.assertIn("README.zh-CN.md", en)
        self.assertIn("README.md", zh)
        self.assertIn("docs/DEMO_QUICKSTART.md", zh)
        self.assertIn("docs/platform/AI_INSIGHT_BOUNDARY.md", zh)
        self.assertIn("docs/rules/PATTERN_CONTRACT.md", zh)


if __name__ == "__main__":
    unittest.main()

