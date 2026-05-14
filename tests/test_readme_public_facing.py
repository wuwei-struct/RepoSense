import pathlib
import unittest


class TestReadmePublicFacing(unittest.TestCase):
    def test_readme_does_not_contain_internal_directives(self):
        text = pathlib.Path("README.md").read_text(encoding="utf-8")
        forbidden = ["PR-PROD-", "给 IDE", "你现在的目录", "指令包"]
        for s in forbidden:
            self.assertNotIn(s, text, f"README.md should not contain internal text: {s}")

    def test_readme_has_language_switch(self):
        text = pathlib.Path("README.md").read_text(encoding="utf-8")
        self.assertIn("README.zh-CN.md", text)
        zh = pathlib.Path("README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("./README.md", zh)


if __name__ == "__main__":
    unittest.main()
