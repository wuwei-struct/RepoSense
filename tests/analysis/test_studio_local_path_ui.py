import os
import unittest


class StudioLocalPathUiTest(unittest.TestCase):
    def test_index_has_local_path_controls(self):
        path = os.path.join("webui", "studio", "index.html")
        self.assertTrue(os.path.isfile(path), f"missing file: {path}")
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        markers = [
            "Analyze local path",
            "Analyze local repository path",
            "local-repo-path",
            "/api/projects/import-path",
        ]
        for marker in markers:
            self.assertIn(marker, text, f"index.html missing marker: {marker}")


if __name__ == "__main__":
    unittest.main()
