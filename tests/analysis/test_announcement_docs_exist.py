import os
import unittest


class AnnouncementDocsExistTest(unittest.TestCase):
    def test_announcement_files_exist(self):
        files = [
            "docs/release/ANNOUNCEMENT_LONG_zh.md",
            "docs/release/ANNOUNCEMENT_SHORT_zh.md",
        ]
        for path in files:
            self.assertTrue(os.path.isfile(path), f"missing announcement doc: {path}")

    def test_long_announcement_has_key_markers(self):
        with open("docs/release/ANNOUNCEMENT_LONG_zh.md", "r", encoding="utf-8") as f:
            text = f.read()

        self.assertIn("Engineering Intelligence System", text)
        self.assertIn("Facts", text)
        self.assertIn("Patterns", text)
        self.assertIn("Insights", text)
        self.assertIn("Facts first, source on demand", text)

    def test_short_announcement_has_three_versions(self):
        with open("docs/release/ANNOUNCEMENT_SHORT_zh.md", "r", encoding="utf-8") as f:
            text = f.read()

        self.assertIn("版本 1", text)
        self.assertIn("版本 2", text)
        self.assertIn("版本 3", text)


if __name__ == "__main__":
    unittest.main()
