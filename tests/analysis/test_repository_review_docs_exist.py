import os
import unittest


class RepositoryReviewDocsExistTest(unittest.TestCase):
    def test_review_docs_and_entrypoints(self):
        path = "docs/review/REPOSITORY_REVIEW_MODE.md"
        self.assertTrue(os.path.isfile(path), f"missing file: {path}")
        with open(path, "r", encoding="utf-8") as f:
            doc = f.read()
        for marker in ["Repository Review Mode", "human_review_required.md", "Code Health Radar", "Permission Auditor"]:
            self.assertIn(marker, doc)

        with open("README.md", "r", encoding="utf-8") as f:
            readme = f.read()
        with open("docs/INDEX.md", "r", encoding="utf-8") as f:
            index = f.read()
        self.assertIn("docs/review/REPOSITORY_REVIEW_MODE.md", readme)
        self.assertIn("review/REPOSITORY_REVIEW_MODE.md", index)


if __name__ == "__main__":
    unittest.main()
