import os
import unittest


class ReadmeQuickstartExistsTest(unittest.TestCase):
    def test_readme_has_quickstart_demo_command(self):
        with open("README.md", "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn("3-Minute Quickstart", text)
        self.assertIn("tools/demo_run.ps1", text)

    def test_demo_quickstart_doc_exists(self):
        self.assertTrue(os.path.isfile("docs/DEMO_QUICKSTART.md"))
        with open("docs/DEMO_QUICKSTART.md", "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn("tools/demo_run.ps1", text)
        self.assertIn("AI_EXPLAIN", text)


if __name__ == "__main__":
    unittest.main()
