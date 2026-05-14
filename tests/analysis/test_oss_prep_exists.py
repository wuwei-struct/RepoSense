import os
import unittest


class OssPrepExistsTest(unittest.TestCase):
    def test_oss_prep_exists_and_sections(self):
        path = "docs/OSS_PREP.md"
        self.assertTrue(os.path.isfile(path))
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        required = [
            "License Layering Guidance",
            "Third-Party Repository Case Data Boundary",
            "Open-Source Release Checklist",
            "minimal necessary snippets",
            "repo_ref",
        ]
        for marker in required:
            self.assertIn(marker, text, f"OSS_PREP.md missing marker: {marker}")


if __name__ == "__main__":
    unittest.main()
