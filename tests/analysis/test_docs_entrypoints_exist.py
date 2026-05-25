import os
import unittest


class DocsEntrypointsExistTest(unittest.TestCase):
    def test_docs_files_exist(self):
        docs = [
            "docs/ARCHITECTURE.md",
            "docs/DEMO_QUICKSTART.md",
            "docs/studio/STUDIO_UI.md",
            "docs/FACTS_PATTERNS_INSIGHTS.md",
            "docs/LEARN_OVERVIEW.md",
            "docs/AI_GROUNDED_PRINCIPLES.md",
            "docs/OUTPUTS_MAP.md",
        ]
        for p in docs:
            self.assertTrue(os.path.isfile(p), f"missing doc: {p}")

    def test_docs_have_key_headings(self):
        checks = {
            "docs/ARCHITECTURE.md": ["Architecture Overview", "Facts / Patterns / Insights Separation"],
            "docs/FACTS_PATTERNS_INSIGHTS.md": ["Facts, Patterns, Insights", "Facts First, Source On Demand"],
            "docs/LEARN_OVERVIEW.md": ["Learn Overview", "ConceptGraph", "CaseLibrary"],
            "docs/AI_GROUNDED_PRINCIPLES.md": ["AI Grounded Principles", "Facts-only Reasoning by Default"],
            "docs/OUTPUTS_MAP.md": ["Outputs Map", "Facts Outputs", "AI Derived Outputs"],
        }
        for path, required in checks.items():
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            for marker in required:
                self.assertIn(marker, text, f"{path} missing heading marker: {marker}")


if __name__ == "__main__":
    unittest.main()
