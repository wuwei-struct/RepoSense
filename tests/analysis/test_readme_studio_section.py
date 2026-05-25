import os
import unittest


class ReadmeStudioSectionTest(unittest.TestCase):
    def test_readme_en_has_studio_section(self):
        path = "README.md"
        self.assertTrue(os.path.isfile(path), f"missing file: {path}")
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        for marker in ["Studio UI", "reposense studio serve", "ZIP", "local repository path", "http://127.0.0.1:8010"]:
            self.assertIn(marker, text, f"README.md missing marker: {marker}")

    def test_readme_zh_has_studio_section(self):
        path = "README.zh-CN.md"
        self.assertTrue(os.path.isfile(path), f"missing file: {path}")
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        markers = ["Studio UI", "上传仓库 ZIP", "本地仓库路径", "本地开发者 UI", "http://127.0.0.1:8010"]
        for marker in markers:
            self.assertIn(marker, text, f"README.zh-CN.md missing marker: {marker}")


if __name__ == "__main__":
    unittest.main()
