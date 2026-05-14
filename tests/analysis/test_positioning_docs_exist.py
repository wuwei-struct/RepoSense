import os
import unittest


class PositioningRoadmapDocsExistTest(unittest.TestCase):
    def test_positioning_and_roadmap_docs_exist(self):
        files = [
            "docs/positioning/BACKEND_VERIFIER.md",
            "docs/positioning/OPEN_SOURCE_STRATEGY.md",
            "docs/architecture/COMMERCIAL_BOUNDARY.md",
            "docs/roadmap/ROADMAP.md",
        ]
        for path in files:
            self.assertTrue(os.path.isfile(path), f"missing doc: {path}")

    def test_positioning_markers(self):
        with open("docs/positioning/BACKEND_VERIFIER.md", "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn("backend transaction and side-effect verifier", text.lower())
        self.assertIn("AI-generated", text)

        with open("docs/positioning/OPEN_SOURCE_STRATEGY.md", "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn("Pattern detection logic", text)
        self.assertIn("reserved", text.lower())

        with open("docs/roadmap/ROADMAP.md", "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn("Phase 1: Backend Verifier OSS", text)
        self.assertIn("Phase 5: Team / Enterprise Reporting", text)


if __name__ == "__main__":
    unittest.main()

