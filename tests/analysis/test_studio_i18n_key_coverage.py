import re
import unittest
from pathlib import Path


KEY_RE = re.compile(r"^\s*'([^']+)'\s*:", re.MULTILINE)


class StudioI18nKeyCoverageTest(unittest.TestCase):
    def setUp(self):
        self.english_text = Path("webui/studio/locales/en-US.js").read_text(encoding="utf-8")
        self.chinese_text = Path("webui/studio/locales/zh-CN.js").read_text(encoding="utf-8")
        self.english = KEY_RE.findall(self.english_text)
        self.chinese = KEY_RE.findall(self.chinese_text)

    def test_keys_are_unique_and_core_chinese_keys_exist(self):
        self.assertEqual(len(self.english), len(set(self.english)))
        self.assertEqual(len(self.chinese), len(set(self.chinese)))
        required = {
            "nav.home", "home.title", "analyze.title", "pipeline.scanning_facts",
            "workbench.overview", "workbench.human", "workbench.architecture",
            "workbench.transactions", "workbench.queue", "workbench.permission",
            "workbench.health", "workbench.validation", "workbench.context",
            "workbench.artifacts", "artifact.recommendedFirst", "artifact.notGenerated",
        }
        self.assertTrue(required.issubset(set(self.english)))
        self.assertTrue(required.issubset(set(self.chinese)))

    def test_catalogs_do_not_define_null_or_undefined_labels(self):
        for text in (self.english_text, self.chinese_text):
            self.assertNotRegex(text, r":\s*(?:undefined|null)\s*[,}]" )
        self.assertIn("{count}", self.english_text)
        self.assertIn("{count}", self.chinese_text)


if __name__ == "__main__":
    unittest.main()
