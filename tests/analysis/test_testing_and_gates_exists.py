import os
import unittest


class TestingAndGatesExistsTest(unittest.TestCase):
    def test_testing_and_gates_exists_and_sections(self):
        path = "docs/TESTING_AND_GATES.md"
        self.assertTrue(os.path.isfile(path))
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        required = [
            "ci run",
            "verify --strict",
            "gate",
            "patch exports",
            "run manifest",
            "Demo Script",
            "Learn Tests",
            "AI Tests",
            "Studio/UI Snapshot Tests",
        ]
        for marker in required:
            self.assertIn(marker, text, f"TESTING_AND_GATES.md missing marker: {marker}")


if __name__ == "__main__":
    unittest.main()
