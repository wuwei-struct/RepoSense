import os
import unittest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class CodeHealthDocsExistTest(unittest.TestCase):
    def test_docs_and_readme_entries_exist(self):
        doc = os.path.join(ROOT, "docs", "review", "CODE_HEALTH_RADAR.md")
        self.assertTrue(os.path.isfile(doc))
        with open(doc, "r", encoding="utf-8") as f:
            text = f.read()
        lower = text.lower()
        for phrase in ["code health radar", "chd-001", "chd-005", "limitations", "reposense health scan"]:
            self.assertIn(phrase, lower)
        for path in ["README.md", "README.zh-CN.md", os.path.join("docs", "INDEX.md"), os.path.join("docs", "review", "REPOSITORY_REVIEW_MODE.md")]:
            with open(os.path.join(ROOT, path), "r", encoding="utf-8") as f:
                self.assertIn("CODE_HEALTH_RADAR.md", f.read())


if __name__ == "__main__":
    unittest.main()
