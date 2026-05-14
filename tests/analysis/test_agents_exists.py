import os
import unittest


class AgentsExistsTest(unittest.TestCase):
    def test_agents_file_exists(self):
        self.assertTrue(os.path.isfile("AGENTS.md"))

    def test_agents_required_sections(self):
        with open("AGENTS.md", "r", encoding="utf-8") as f:
            text = f.read()

        required = [
            "D:\\安装\\Python\\python.exe",
            "python",
            "py -3",
            "Required Verification Chain",
            "Do not claim \"validated\" or \"passed\"",
            "Prohibited Actions",
            "run manifest",
        ]
        for marker in required:
            self.assertIn(marker, text, f"AGENTS.md missing marker: {marker}")


if __name__ == "__main__":
    unittest.main()
