import unittest
from pathlib import Path


class StudioLanguageSwitcherUiTest(unittest.TestCase):
    def test_switcher_is_accessible_and_has_no_flag_language_selector(self):
        index = Path("webui/studio/index.html").read_text(encoding="utf-8")
        i18n = Path("webui/studio/i18n.js").read_text(encoding="utf-8")
        self.assertIn('id="language-switcher-mount"', index)
        self.assertIn("role=\"group\"", i18n)
        self.assertIn("aria-label", i18n)
        self.assertIn("aria-pressed", i18n)
        for flag in ("🇨🇳", "🇺🇸", "flag-icon"):
            self.assertNotIn(flag, index + i18n)

    def test_locale_rerender_preserves_application_state_objects(self):
        shell = Path("webui/studio/app-shell.js").read_text(encoding="utf-8")
        form = Path("webui/studio/analyze-form.js").read_text(encoding="utf-8")
        workbench = Path("webui/studio/run-workbench.js").read_text(encoding="utf-8")
        self.assertIn("subscribeLocaleChange", shell)
        self.assertIn("state.currentRun", shell)
        self.assertIn("const formState", form)
        self.assertIn("getActiveTab", workbench)


if __name__ == "__main__":
    unittest.main()
