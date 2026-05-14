import os
import unittest


class ReadmeDocsEntrySlimTest(unittest.TestCase):
    def test_readme_has_slim_core_docs_links(self):
        with open("README.md", "r", encoding="utf-8") as f:
            text = f.read()

        required = [
            "docs/DEMO_QUICKSTART.md",
            "docs/ARCHITECTURE.md",
            "docs/reports/BACKEND_VERIFIER_REPORT.md",
            "docs/context-pack/CONTEXT_PACK_SPEC.md",
            "docs/AI_GROUNDED_PRINCIPLES.md",
            "docs/INDEX.md",
        ]
        for marker in required:
            self.assertIn(marker, text, f"README missing core docs link: {marker}")

        self.assertNotIn("docs/release/RELEASE_CANDIDATE_v0.1.0.md", text)
        self.assertNotIn("docs/rules/RULE_AUTHORING_GUIDE.md", text)

    def test_docs_index_exists_and_has_broad_index(self):
        path = "docs/INDEX.md"
        self.assertTrue(os.path.isfile(path), f"missing file: {path}")
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        markers = [
            "Docs Index",
            "Core Entry Points",
            "Product and Positioning",
            "Release and Announcement",
            "docs/rules/PATTERN_CONTRACT.md",
            "docs/release/RELEASE_NOTES_v0.1.0.md",
        ]
        for marker in markers:
            self.assertIn(marker, text, f"docs/INDEX.md missing marker: {marker}")


if __name__ == "__main__":
    unittest.main()
