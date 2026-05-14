import os
import re
import unittest


class DemoAssetsFilesExistTest(unittest.TestCase):
    def test_demo_assets_docs_exist(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.assertTrue(os.path.isfile(os.path.join(root, "docs", "assets", "demo", "demo-outputs.md")))
        self.assertTrue(os.path.isfile(os.path.join(root, "docs", "assets", "demo", "product-flow.md")))
        self.assertTrue(os.path.isfile(os.path.join(root, "docs", "assets", "screenshots", "CAPTURE_PLAN.md")))
        self.assertTrue(os.path.isfile(os.path.join(root, "docs", "assets", "screenshots", "MANUAL_CAPTURE_CHECKLIST.md")))
        cap = os.path.join(root, "docs", "assets", "screenshots", "CAPTURE_PLAN.md")
        mcc = os.path.join(root, "docs", "assets", "screenshots", "MANUAL_CAPTURE_CHECKLIST.md")
        with open(cap, "r", encoding="utf-8") as f:
            cap_txt = f.read()
        with open(mcc, "r", encoding="utf-8") as f:
            mcc_txt = f.read()
        self.assertIn(".reposense_demo_release_assets_current", cap_txt)
        self.assertIn("<latest-run>", cap_txt)
        self.assertIn(".reposense_demo_release_assets_current", mcc_txt)
        self.assertIn("<latest-run>", mcc_txt)

    def test_asset_index_lists_six_recommended_screenshots(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        idx = os.path.join(root, "docs", "assets", "ASSET_INDEX.md")
        self.assertTrue(os.path.isfile(idx))
        with open(idx, "r", encoding="utf-8") as f:
            txt = f.read()
        required = [
            "report-overview.png",
            "backend-events.png",
            "api-surface.png",
            "learn-overview.png",
            "ai-risks-panel.png",
            "ai-explain-detail.png",
        ]
        for m in required:
            self.assertIn(m, txt)
        self.assertTrue(
            "pending_manual_capture" in txt or "pending_data_fixture" in txt or "captured" in txt
        )

    def test_learn_screenshot_not_falsely_marked_captured(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        idx = os.path.join(root, "docs", "assets", "ASSET_INDEX.md")
        with open(idx, "r", encoding="utf-8") as f:
            txt = f.read()
        if re.search(r"\|\s*learn-overview\s*\|.*\|\s*captured\s*\|", txt):
            img = os.path.join(root, "docs", "assets", "screenshots", "learn-overview.png")
            self.assertTrue(
                os.path.isfile(img),
                "learn-overview is marked captured but PNG file is missing",
            )


if __name__ == "__main__":
    unittest.main()
