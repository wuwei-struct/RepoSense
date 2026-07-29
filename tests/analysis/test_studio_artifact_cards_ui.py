import os
import unittest


class StudioArtifactCardsUiTest(unittest.TestCase):
    def test_cards_are_loaded_from_a_separate_module(self):
        root = os.path.join(os.getcwd(), "webui", "studio")
        with open(os.path.join(root, "index.html"), "r", encoding="utf-8") as handle:
            index = handle.read()
        with open(os.path.join(root, "artifact-cards.js"), "r", encoding="utf-8") as handle:
            script = handle.read()
        with open(os.path.join(root, "artifact-cards.css"), "r", encoding="utf-8") as handle:
            css = handle.read()
        self.assertIn('/artifact-cards.js', index)
        self.assertIn('/artifact-cards.css', index)
        self.assertIn('current-artifact-cards', index)
        self.assertNotIn('function renderReviewPanel', index)
        for marker in [
            'Recommended First',
            'Evidence Integrity',
            'Strict Verify',
            'Quality Gate',
            'Human Review Required',
            'Copy relative path',
            'StudioArtifactCards',
        ]:
            self.assertIn(marker, script)
        self.assertIn('.artifact-card', css)


if __name__ == "__main__":
    unittest.main()
