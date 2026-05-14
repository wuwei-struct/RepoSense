import os
import unittest


class ReleaseNotesExistTest(unittest.TestCase):
    def test_release_notes_file_exists(self):
        path = "docs/release/RELEASE_NOTES_v0.1.0.md"
        self.assertTrue(os.path.isfile(path), f"missing release notes: {path}")

    def test_release_notes_has_key_sections(self):
        path = "docs/release/RELEASE_NOTES_v0.1.0.md"
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().lower()

        required_markers = [
            "included in this release",
            "key capabilities",
            "trust boundaries",
            "known limitations",
            "demo",
        ]
        for marker in required_markers:
            self.assertIn(marker, text, f"release notes missing marker: {marker}")


if __name__ == "__main__":
    unittest.main()
