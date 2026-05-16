import os
import unittest


class DemoAssetsIndexExistsTest(unittest.TestCase):
    def test_asset_index_exists_and_core_entries(self):
        idx = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "assets", "ASSET_INDEX.md"))
        self.assertTrue(os.path.isfile(idx))
        with open(idx, "r", encoding="utf-8") as f:
            txt = f.read()
        self.assertIn("report-overview", txt)
        self.assertIn("backend-events", txt)
        self.assertIn("api-surface", txt)
        self.assertIn("backend-verifier-report", txt)
        self.assertIn("demo-outputs", txt)
        self.assertIn("learn-overview", txt)
        self.assertIn("ai-risks-panel", txt)
        self.assertIn("ai-explain-detail", txt)


if __name__ == "__main__":
    unittest.main()
