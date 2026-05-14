import os
import unittest


class ReleaseChecklistExistsTest(unittest.TestCase):
    def test_release_checklist_exists_and_sections(self):
        p = "docs/RELEASE_CHECKLIST.md"
        self.assertTrue(os.path.isfile(p))
        with open(p, "r", encoding="utf-8") as f:
            text = f.read()

        required = [
            "Demo",
            "Testing and Gates",
            "Documentation",
            "OSS and Compliance",
            "Release Artifacts",
            "run_manifest",
        ]
        for marker in required:
            self.assertIn(marker, text, f"release checklist missing marker: {marker}")


if __name__ == "__main__":
    unittest.main()
