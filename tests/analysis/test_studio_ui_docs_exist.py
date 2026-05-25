import os
import unittest


class StudioUiDocsExistTest(unittest.TestCase):
    def test_studio_ui_doc_exists_and_contains_markers(self):
        path = "docs/studio/STUDIO_UI.md"
        self.assertTrue(os.path.isfile(path), f"missing file: {path}")
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        markers = [
            "reposense studio serve",
            "ZIP",
            "local repository path",
            "report.html",
            "Context Pack",
            "webui/studio/index.html",
            "reposense/studio/server.py",
            "local Studio UI",
        ]
        for marker in markers:
            self.assertIn(marker, text, f"STUDIO_UI.md missing marker: {marker}")


if __name__ == "__main__":
    unittest.main()
