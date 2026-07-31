import unittest
from pathlib import Path


class StudioI18nDocsTest(unittest.TestCase):
    def test_i18n_contract_and_index_are_documented(self):
        doc = Path("docs/studio/STUDIO_I18N.md").read_text(encoding="utf-8")
        for marker in (
            "zh-CN", "en-US", "reposense.studio.locale", "navigator.language",
            "English is the fallback", "Stable data boundary", "does not prove",
        ):
            self.assertIn(marker, doc)
        self.assertIn("STUDIO_I18N.md", Path("docs/INDEX.md").read_text(encoding="utf-8"))

    def test_readmes_and_visual_qa_record_bilingual_boundary(self):
        self.assertIn("English and Simplified Chinese", Path("README.md").read_text(encoding="utf-8"))
        self.assertIn("英文和简体中文", Path("README.zh-CN.md").read_text(encoding="utf-8"))
        qa = Path("docs/validation/STUDIO_VISUAL_QA_V02.md").read_text(encoding="utf-8")
        self.assertIn("Studio 2.0 bilingual QA record", qa)
        self.assertIn("historical", qa)


if __name__ == "__main__":
    unittest.main()
