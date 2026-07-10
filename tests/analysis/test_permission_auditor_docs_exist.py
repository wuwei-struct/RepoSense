import os
import unittest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class PermissionAuditorDocsExistTest(unittest.TestCase):
    def test_docs_and_readme_entries_exist(self):
        doc = os.path.join(ROOT, "docs", "review", "PERMISSION_AUDITOR.md")
        self.assertTrue(os.path.isfile(doc))
        with open(doc, "r", encoding="utf-8") as f:
            text = f.read().lower()
        for phrase in ["permission auditor", "authz-001", "authz-005", "limitations", "reposense authz scan"]:
            self.assertIn(phrase, text)
        for path in ["README.md", "README.zh-CN.md", os.path.join("docs", "INDEX.md"), os.path.join("docs", "review", "REPOSITORY_REVIEW_MODE.md")]:
            with open(os.path.join(ROOT, path), "r", encoding="utf-8") as f:
                self.assertIn("PERMISSION_AUDITOR.md", f.read())


if __name__ == "__main__":
    unittest.main()

