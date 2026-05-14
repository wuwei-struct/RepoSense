import unittest


class ReadmeStorySectionsTest(unittest.TestCase):
    def test_story_structure_markers(self):
        with open("README.md", "r", encoding="utf-8") as f:
            text = f.read()

        markers = [
            "first backend version quickly",
            "maintainability, upgrade confidence",
            "upgrade context",
            "OSS Local Capabilities",
            "Roadmap / Hosted Enhancements",
            "After Running the Demo, You Will See",
        ]
        for marker in markers:
            self.assertIn(marker, text, f"README missing story marker: {marker}")


if __name__ == "__main__":
    unittest.main()
