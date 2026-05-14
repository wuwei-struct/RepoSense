import unittest


class ContextPackDocsSectionsTest(unittest.TestCase):
    def test_context_pack_spec_sections(self):
        with open("docs/context-pack/CONTEXT_PACK_SPEC.md", "r", encoding="utf-8") as f:
            text = f.read().lower()
        self.assertIn("what is context pack", text)
        self.assertIn("directory structure", text)
        self.assertIn("facts", text)
        self.assertIn("derived", text)

    def test_ai_usage_sections(self):
        with open("docs/context-pack/AI_ASSISTANT_USAGE.md", "r", encoding="utf-8") as f:
            text = f.read().lower()
        self.assertIn("ai assistant usage", text)
        self.assertIn("facts first, source on demand", text)
        self.assertIn("do not", text)

    def test_examples_sections_and_readme_links(self):
        with open("docs/context-pack/EXAMPLES.md", "r", encoding="utf-8") as f:
            text = f.read().lower()
        self.assertIn("examples", text)
        self.assertIn("facts-only then drilldown", text)

        with open("README.md", "r", encoding="utf-8") as f:
            rd = f.read()
        with open("docs/INDEX.md", "r", encoding="utf-8") as f:
            idx = f.read()
        self.assertIn("docs/context-pack/CONTEXT_PACK_SPEC.md", rd)
        self.assertIn("docs/context-pack/AI_ASSISTANT_USAGE.md", idx)
        self.assertIn("docs/context-pack/EXAMPLES.md", idx)


if __name__ == "__main__":
    unittest.main()
