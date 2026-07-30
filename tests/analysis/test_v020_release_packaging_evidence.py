import unittest
from pathlib import Path


AUDIT = Path("docs/release/V0_2_0_RELEASE_READINESS_AUDIT.md")


class V020ReleasePackagingEvidenceTest(unittest.TestCase):
    def test_gate_a_and_gate_b_evidence_is_recorded(self):
        text = AUDIT.read_text(encoding="utf-8")
        for marker in (
            "`asset_packaging` | pass",
            "`target_install_smoke` | pass",
            "52/52",
            "386,801 bytes",
            "243",
            "Two consecutive fresh-venv",
            "`pip check`",
            "CPython 3.11 on Windows AMD64",
        ):
            self.assertIn(marker, text)

    def test_real_repository_commits_and_licenses_are_recorded(self):
        text = AUDIT.read_text(encoding="utf-8")
        expected = {
            "549cc37a3925ab87a4e61b45efb3b86d2d8e234e": "MIT",
            "c7b5f5e9e90af2e5b94a40dd77b2a53dc33f67bd": "Apache-2.0",
            "147231b54ed8f8a7f3a0b5110db757a39650892c": "MIT",
            "46492f9147673513338505049eff09bc796dd166": "Apache-2.0",
        }
        for commit, license_name in expected.items():
            self.assertIn(commit, text)
            self.assertIn(license_name, text)

    def test_resolved_blockers_and_remaining_warnings_are_recorded(self):
        text = AUDIT.read_text(encoding="utf-8")
        for marker in (
            "Wheel missing runtime assets | Resolved",
            "No controlled fresh-venv offline install | Resolved",
            "Studio run APIs disclosed local paths | Resolved",
            "local-path leaks: 0",
            "ResourceWarning",
            "api.missing_in_spec_count=3",
            "No pinned real repository contains statically explicit",
            "different ZIP SHA-256",
        ):
            self.assertIn(marker, text)

    def test_release_plan_requires_remote_refresh_before_push(self):
        plan = Path("docs/release/V0_2_0_RELEASE_PLAN.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("## 8. Remote Refresh", plan)
        self.assertIn("git fetch --prune", plan)
        self.assertLess(plan.index("## 8. Remote Refresh"), plan.index("## 9. Push"))


if __name__ == "__main__":
    unittest.main()
