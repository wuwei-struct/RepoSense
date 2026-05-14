import os
import unittest


class ReleaseChecklistPublicExistsTest(unittest.TestCase):
    def test_release_checklist_public_exists(self):
        path = "docs/release/RELEASE_CHECKLIST_PUBLIC.md"
        self.assertTrue(os.path.isfile(path), f"missing release checklist: {path}")

    def test_release_checklist_public_has_sections(self):
        path = "docs/release/RELEASE_CHECKLIST_PUBLIC.md"
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().lower()

        markers = [
            "version / tag",
            "demo verification",
            "key outputs verification",
            "docs verification",
            "assets verification",
            "oss / license verification",
            "known limitations review",
            "release notes / announcement ready",
            "post-release follow-ups",
        ]
        for m in markers:
            self.assertIn(m, text, f"missing section marker: {m}")


if __name__ == "__main__":
    unittest.main()
