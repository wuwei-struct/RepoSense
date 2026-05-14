import os
import unittest


class PRTemplateExistsTest(unittest.TestCase):
    def test_pr_template_exists_and_sections(self):
        p = ".github/PULL_REQUEST_TEMPLATE.md"
        self.assertTrue(os.path.isfile(p))
        with open(p, "r", encoding="utf-8") as f:
            text = f.read()

        required = [
            "Change Summary",
            "Testing and Validation",
            "Risks and Boundaries",
            "Grounded / Truth-Source Checks",
            "schema_version",
            "run manifest",
        ]
        for marker in required:
            self.assertIn(marker, text, f"PR template missing marker: {marker}")


if __name__ == "__main__":
    unittest.main()
