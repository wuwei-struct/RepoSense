import re
import unittest
from pathlib import Path


class StudioI18nCatalogTest(unittest.TestCase):
    def setUp(self):
        self.root = Path("webui/studio")
        self.english = (self.root / "locales/en-US.js").read_text(encoding="utf-8")
        self.chinese = (self.root / "locales/zh-CN.js").read_text(encoding="utf-8")

    def test_supported_catalogs_are_separate_resources(self):
        self.assertIn("['en-US']", self.english)
        self.assertIn("['zh-CN']", self.chinese)
        self.assertNotIn("<section", self.english)
        self.assertNotIn("<section", self.chinese)

    def test_every_catalog_artifact_has_chinese_name_and_description(self):
        catalog = Path("reposense/studio/artifact_catalog.py").read_text(encoding="utf-8")
        artifact_ids = re.findall(r'"artifact_id": "([a-z0-9_]+)"', catalog)
        self.assertGreaterEqual(len(artifact_ids), 20)
        for artifact_id in artifact_ids:
            self.assertIn(f"'artifacts.{artifact_id}.name'", self.chinese)
            self.assertIn(f"'artifacts.{artifact_id}.description'", self.chinese)


if __name__ == "__main__":
    unittest.main()
