import os
import unittest


class AIInsightBoundaryDocsExistTest(unittest.TestCase):
    def test_ai_insight_boundary_doc_exists_and_markers(self):
        path = "docs/platform/AI_INSIGHT_BOUNDARY.md"
        self.assertTrue(os.path.isfile(path), f"missing doc: {path}")
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().lower()
        self.assertIn("oss layer", text)
        self.assertIn("hosted / commercial layer", text)
        self.assertIn("evidence-backed", text)
        self.assertIn("repair suggestions", text)


if __name__ == "__main__":
    unittest.main()

