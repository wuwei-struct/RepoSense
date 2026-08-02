import unittest
from pathlib import Path

from reposense.studio.analysis_profiles import list_public_analysis_profiles
from reposense.studio.public_run_payload import build_public_run_payload


class StudioI18nWorkbenchTest(unittest.TestCase):
    def test_workbench_surfaces_use_translation_keys(self):
        sources = "\n".join(
            Path(f"webui/studio/{name}").read_text(encoding="utf-8")
            for name in ("app-shell.js", "analyze-form.js", "run-workbench.js", "artifact-cards.js")
        )
        for marker in (
            "home.title", "analyze.title", "pipeline.${step.step_id}",
            "workbench.${id}", "artifact.recommendedFirst", "artifact.copyPath",
        ):
            self.assertIn(marker, sources)

    def test_api_ids_remain_language_neutral(self):
        profiles = list_public_analysis_profiles()
        self.assertEqual({item["profile_id"] for item in profiles}, {"quick_scan", "full_review"})
        payload = build_public_run_payload({
            "run_id": "run-i18n",
            "status": "running",
            "profile": profiles[0],
            "pipeline": {"profile_id": "full_review", "steps": []},
        })
        self.assertNotIn("locale", payload)
        self.assertNotIn("translations", payload)
        self.assertEqual(payload["status"], "running")


if __name__ == "__main__":
    unittest.main()
