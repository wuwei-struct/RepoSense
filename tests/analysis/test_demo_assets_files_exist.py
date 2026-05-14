import os
import unittest


class DemoAssetsFilesExistTest(unittest.TestCase):
    def test_demo_assets_docs_exist(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.assertTrue(os.path.isfile(os.path.join(root, "docs", "assets", "demo", "demo-outputs.md")))
        self.assertTrue(os.path.isfile(os.path.join(root, "docs", "assets", "demo", "product-flow.md")))
        self.assertTrue(os.path.isfile(os.path.join(root, "docs", "assets", "screenshots", "CAPTURE_PLAN.md")))
        self.assertTrue(os.path.isfile(os.path.join(root, "docs", "assets", "screenshots", "MANUAL_CAPTURE_CHECKLIST.md")))


if __name__ == "__main__":
    unittest.main()
