import os
import unittest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class ContextPackReviewDocsExistTest(unittest.TestCase):
    def test_review_section_docs_exist(self):
        doc = os.path.join(ROOT, "docs", "context-pack", "REVIEW_SECTION.md")
        self.assertTrue(os.path.isfile(doc))
        with open(doc, "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn("REVIEW section", text)
        self.assertIn("AI Maintenance Constraints", text)
        with open(os.path.join(ROOT, "docs", "context-pack", "CONTEXT_PACK_SPEC.md"), "r", encoding="utf-8") as f:
            self.assertIn("REVIEW", f.read())
        with open(os.path.join(ROOT, "docs", "context-pack", "AI_ASSISTANT_USAGE.md"), "r", encoding="utf-8") as f:
            self.assertIn("REVIEW/README.md", f.read())
        with open(os.path.join(ROOT, "docs", "INDEX.md"), "r", encoding="utf-8") as f:
            self.assertIn("REVIEW_SECTION.md", f.read())


if __name__ == "__main__":
    unittest.main()

