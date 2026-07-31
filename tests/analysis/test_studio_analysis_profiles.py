import unittest

from reposense.studio.analysis_profiles import (
    DEFAULT_ANALYSIS_PROFILE,
    get_analysis_profile,
    list_public_analysis_profiles,
)


class StudioAnalysisProfilesTest(unittest.TestCase):
    def test_profiles_are_stable_and_full_review_is_default(self):
        profiles = list_public_analysis_profiles()
        self.assertEqual(DEFAULT_ANALYSIS_PROFILE, "full_review")
        self.assertEqual([item["profile_id"] for item in profiles], [
            "full_review",
            "quick_scan",
        ])
        self.assertTrue(profiles[0]["recommended"])
        self.assertFalse(profiles[1]["recommended"])
        self.assertTrue(profiles[0]["capabilities"]["permission_review"])
        self.assertFalse(profiles[1]["capabilities"]["permission_review"])

    def test_public_profiles_do_not_expose_runtime_paths(self):
        serialized = repr(list_public_analysis_profiles()).lower()
        for marker in ("ruleset_path", "budget_path", "specs_path", "gate_path"):
            self.assertNotIn(marker, serialized)
        internal = get_analysis_profile("full_review")
        self.assertTrue(internal["ruleset_path"])
        self.assertTrue(internal["specs_path"])

    def test_unknown_profile_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown_analysis_profile"):
            get_analysis_profile("unknown")


if __name__ == "__main__":
    unittest.main()
