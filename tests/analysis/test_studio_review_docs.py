import os
import unittest


class StudioReviewDocsTest(unittest.TestCase):
    def test_studio_docs_describe_review_panel(self):
        with open(os.path.join(os.getcwd(), "docs", "studio", "STUDIO_UI.md"), "r", encoding="utf-8") as f:
            doc = f.read()
        for marker in [
            "Repository Review panel",
            "human_review_required.md",
            "Code Health",
            "Permission Auditor",
            "AuthZ Matrix",
            "does not replace human code review",
        ]:
            self.assertIn(marker, doc)

    def test_readmes_mention_studio_review_artifacts(self):
        with open(os.path.join(os.getcwd(), "README.md"), "r", encoding="utf-8") as f:
            readme = f.read()
        for marker in ["Repository Review", "human review required", "Code Health", "Permission Review", "AuthZ Matrix"]:
            self.assertIn(marker, readme)

        with open(os.path.join(os.getcwd(), "README.zh-CN.md"), "r", encoding="utf-8") as f:
            readme_zh = f.read()
        for marker in ["Repository Review", "人工复核", "Code Health", "Permission Review", "AuthZ Matrix"]:
            self.assertIn(marker, readme_zh)


if __name__ == "__main__":
    unittest.main()
