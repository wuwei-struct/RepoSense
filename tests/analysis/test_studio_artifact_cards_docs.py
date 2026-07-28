import os
import unittest


class StudioArtifactCardsDocsTest(unittest.TestCase):
    def test_docs_explain_read_only_prioritized_cards(self):
        path = os.path.join(os.getcwd(), "docs", "studio", "STUDIO_UI.md")
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        for marker in [
            'Run Artifact Cards',
            'Recommended First',
            'Evidence Integrity',
            'Strict Verify',
            'not generated',
            'does not generate, modify, or validate artifacts',
        ]:
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
