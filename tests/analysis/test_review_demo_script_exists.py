import os
import unittest


class ReviewDemoScriptExistsTest(unittest.TestCase):
    def test_review_demo_script_exists_and_mentions_pipeline(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        path = os.path.join(root, "tools", "review_demo.ps1")
        self.assertTrue(os.path.isfile(path))
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        for marker in [
            ".reposense_review_demo",
            "current",
            "review report",
            "health scan",
            "authz scan",
            "authz matrix",
        ]:
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
