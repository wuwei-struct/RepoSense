import unittest


class ReadmeProductSectionsTest(unittest.TestCase):
    def test_readme_product_sections_present(self):
        with open("README.md", "r", encoding="utf-8") as f:
            text = f.read()

        required = [
            "RepoSense turns repositories into auditable engineering facts",
            "3-Minute Quickstart",
            "Facts",
            "Patterns",
            "Insights",
            "Learn",
            "AI Grounded Principles",
            "Context Pack / Upgrade Context",
            "FAQ",
            "tools/demo_run.ps1",
            "docs/ARCHITECTURE.md",
            "docs/INDEX.md",
        ]
        for marker in required:
            self.assertIn(marker, text, f"README missing marker: {marker}")


if __name__ == "__main__":
    unittest.main()
