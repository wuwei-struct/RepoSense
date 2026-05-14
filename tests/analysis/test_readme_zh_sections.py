import os
import unittest


class ReadmeZhSectionsTest(unittest.TestCase):
    def test_readme_zh_exists_and_sections(self):
        path = "README.zh-CN.md"
        self.assertTrue(os.path.isfile(path), f"missing file: {path}")
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        markers = [
            "后端事务、副作用与升级上下文系统",
            "为什么需要 RepoSense",
            "后续维护",
            "升级上下文",
            "已落地能力",
            "路线图 / 托管增强",
            "3 分钟 Quickstart",
            "边界说明",
            "Facts",
            "Patterns",
            "Insights",
            "核心文档入口",
            "tools/demo_run.ps1",
        ]
        for m in markers:
            self.assertIn(m, text, f"README.zh-CN missing marker: {m}")


if __name__ == "__main__":
    unittest.main()
