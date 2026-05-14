import os
import unittest


class DemoAssetsIndexExistsTest(unittest.TestCase):
    def test_asset_index_exists_and_core_entries(self):
        idx = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "assets", "ASSET_INDEX.md"))
        self.assertTrue(os.path.isfile(idx))
        txt = open(idx, "r", encoding="utf-8").read()
        self.assertIn("report-overview", txt)
        self.assertIn("learn-overview", txt)
        self.assertIn("ai-risks-panel", txt)
        self.assertIn("ai-explain-detail", txt)


if __name__ == "__main__":
    unittest.main()
