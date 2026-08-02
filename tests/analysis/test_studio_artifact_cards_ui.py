import os
import re
import unittest


class StudioArtifactCardsUiTest(unittest.TestCase):
    def test_cards_are_loaded_from_a_separate_module(self):
        root = os.path.join(os.getcwd(), "webui", "studio")
        with open(os.path.join(root, "index.html"), "r", encoding="utf-8") as handle:
            index = handle.read()
        with open(os.path.join(root, "artifact-cards.js"), "r", encoding="utf-8") as handle:
            script = handle.read()
        with open(os.path.join(root, "artifact-cards.css"), "r", encoding="utf-8") as handle:
            css = handle.read()
        catalogs = {}
        for locale in ("en-US", "zh-CN"):
            with open(
                os.path.join(root, "locales", f"{locale}.js"),
                "r",
                encoding="utf-8",
            ) as handle:
                catalogs[locale] = dict(
                    re.findall(r"['\"]([^'\"]+)['\"]\s*:\s*['\"]([^'\"]*)['\"]", handle.read())
                )

        self.assertIn('/artifact-cards.js', index)
        self.assertIn('/artifact-cards.css', index)
        self.assertIn('current-artifact-cards', index)
        self.assertNotIn('function renderReviewPanel', index)
        for marker in [
            "t('artifact.recommendedFirst')",
            "t('artifact.open')",
            "t('artifact.copyPath')",
            "t('artifact.notGenerated')",
            'artifact.group.${group.group_id}',
            'StudioArtifactCards',
        ]:
            self.assertIn(marker, script)

        behavior_keys = (
            'artifact.recommendedFirst',
            'artifact.open',
            'artifact.copyPath',
            'artifact.group.advanced_raw',
            'artifact.notGenerated',
        )
        for locale in ("en-US", "zh-CN"):
            for key in behavior_keys:
                self.assertIn(key, catalogs[locale])
                self.assertTrue(catalogs[locale][key].strip())
        self.assertEqual('Recommended First', catalogs['en-US']['artifact.recommendedFirst'])
        self.assertIn('.artifact-card', css)


if __name__ == "__main__":
    unittest.main()
