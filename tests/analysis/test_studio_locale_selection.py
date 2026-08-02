import unittest
from pathlib import Path


class StudioLocaleSelectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("webui/studio/i18n.js").read_text(encoding="utf-8")

    def test_storage_precedes_browser_language_and_english_is_fallback(self):
        self.assertIn("reposense.studio.locale", self.source)
        self.assertLess(self.source.index("localStorage.getItem"), self.source.index("navigator.language"))
        self.assertIn("startsWith('zh') ? 'zh-CN' : 'en-US'", self.source)
        self.assertIn("SUPPORTED.includes(nextLocale) ? nextLocale : 'en-US'", self.source)

    def test_locale_change_persists_and_translation_interpolates(self):
        self.assertIn("localStorage.setItem(STORAGE_KEY, normalized)", self.source)
        self.assertIn("subscribers.forEach", self.source)
        self.assertRegex(self.source, r"replace\(/\\\{\(\[A-Za-z0-9_\]\+\)\\\}/g")
        self.assertIn("active[key] == null ? english[key] : active[key]", self.source)


if __name__ == "__main__":
    unittest.main()
