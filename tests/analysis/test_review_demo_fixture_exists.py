import os
import unittest


class ReviewDemoFixtureExistsTest(unittest.TestCase):
    def test_review_demo_fixture_has_required_files(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        fixture = os.path.join(root, "tests", "fixtures", "repos", "review_demo_full")
        self.assertTrue(os.path.isdir(fixture))
        self.assertTrue(os.path.isfile(os.path.join(fixture, "reposense.authz.yaml")))
        self.assertTrue(os.path.isfile(os.path.join(fixture, "src", "main", "java", "demo", "ReviewController.java")))
        self.assertTrue(os.path.isfile(os.path.join(fixture, "src", "frontend", "AdminButton.tsx")))

        with open(os.path.join(fixture, "src", "frontend", "AdminButton.tsx"), "r", encoding="utf-8") as f:
            frontend = f.read()
        self.assertIn("isAdmin", frontend)

        with open(os.path.join(fixture, "reposense.authz.yaml"), "r", encoding="utf-8") as f:
            contract = f.read()
        self.assertIn("order:refund", contract)
        self.assertIn("tenant_boundary", contract)


if __name__ == "__main__":
    unittest.main()
