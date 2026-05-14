import os
import unittest


class CiTemplatesSmokeTest(unittest.TestCase):
    def test_templates_exist_and_keys(self):
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        main = os.path.join(base, ".github", "workflows", "reposense-main.yml")
        pr = os.path.join(base, ".github", "workflows", "reposense-pr.yml")
        self.assertTrue(os.path.isfile(main))
        self.assertTrue(os.path.isfile(pr))
        main_text = open(main, "r", encoding="utf-8").read()
        pr_text = open(pr, "r", encoding="utf-8").read()
        self.assertIn("github/codeql-action/upload-sarif@v3", main_text)
        self.assertIn("github/codeql-action/upload-sarif@v3", pr_text)
        self.assertIn("actions/upload-artifact@v4", pr_text)
        self.assertIn("peter-evans/create-or-update-comment@v5", pr_text)


if __name__ == "__main__":
    unittest.main()
