import unittest


class ContributingSectionsTest(unittest.TestCase):
    def test_contributing_sections(self):
        with open("CONTRIBUTING.md", "r", encoding="utf-8") as f:
            text = f.read()

        required = [
            "Before You Start",
            "Local Development Quick Path",
            "Contribution Types",
            "PR Checklist",
            "verify --strict",
            "run manifest",
            "grounded",
            "Facts first",
        ]
        for marker in required:
            self.assertIn(marker, text, f"CONTRIBUTING.md missing marker: {marker}")


if __name__ == "__main__":
    unittest.main()
