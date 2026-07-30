import re
import unittest
from pathlib import Path


RELEASE_DIR = Path("docs/release")
AUDIT = RELEASE_DIR / "V0_2_0_RELEASE_READINESS_AUDIT.md"
PLAN = RELEASE_DIR / "V0_2_0_RELEASE_PLAN.md"
CHANGELOG = RELEASE_DIR / "V0_2_0_CHANGELOG_DRAFT.md"
NOTES = RELEASE_DIR / "V0_2_0_RELEASE_NOTES_DRAFT.md"


class V020ReleaseAuditDocsTest(unittest.TestCase):
    def test_required_documents_and_audit_sections_exist(self):
        for path in (AUDIT, PLAN, CHANGELOG, NOTES):
            self.assertTrue(path.is_file(), str(path))

        text = AUDIT.read_text(encoding="utf-8")
        for heading in (
            "## 1. Audit Scope",
            "## 2. Git / Version State",
            "## 3. Readiness Verdict",
            "## 4. Blocking Issues",
            "## 5. Non-blocking Warnings",
            "## 6. Packaging Gate A / B",
            "## 7. Verified Capabilities",
            "## 8. CLI / UX",
            "## 9. Tests / Gates",
            "## 10. Demo / Studio",
            "## 11. Real Repository Validation",
            "## 12. Documentation / Links",
            "## 13. Claims Matrix",
            "## 14. License / Third-party Content",
            "## 15. Security / Privacy",
            "## 16. Known Limitations",
            "## 17. Required RC Preparation",
            "## 18. Final Recommendation",
        ):
            self.assertIn(heading, text)

    def test_verdict_and_baseline_are_explicit(self):
        text = AUDIT.read_text(encoding="utf-8")
        verdicts = re.findall(
            r"\*\*(READY|READY_WITH_KNOWN_WARNINGS|BLOCKED)\*\*", text
        )
        self.assertEqual(verdicts, ["READY_WITH_KNOWN_WARNINGS"])
        self.assertIn(
            "edb05dcfa08446fcfa5fe6bf163eba97260902c8", text
        )
        self.assertIn(
            "Remote state was not refreshed during this local readiness audit.",
            text,
        )

    def test_public_version_remains_v010_and_v020_is_not_published(self):
        audit = AUDIT.read_text(encoding="utf-8")
        notes = NOTES.read_text(encoding="utf-8").lower()
        pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
        package_init = Path("reposense/__init__.py").read_text(encoding="utf-8")
        self.assertIn("Public OSS tag at audit time: `v0.1.0`", audit)
        self.assertIn('version = "0.1.0"', pyproject)
        self.assertIn('__version__ = "0.1.0"', package_init)
        self.assertIn("v0.2.0 has not been released", notes)
        self.assertNotIn("v0.2.0 is released", notes)
        self.assertNotIn("v0.2.0 has been released", notes)

    def test_plan_and_drafts_have_required_structure(self):
        plan = PLAN.read_text(encoding="utf-8")
        for marker in (
            "## 1. Release Readiness Sign-off",
            "## 3. Version Authority Update",
            "## 8. Remote Refresh",
            "## 13. Rollback / Forward-fix",
            "0.2.0rc1",
        ):
            self.assertIn(marker, plan)

        changelog = CHANGELOG.read_text(encoding="utf-8")
        for marker in (
            "## Added",
            "## Improved",
            "## Fixed",
            "## Validation",
            "## Packaging",
            "## Known Limitations",
        ):
            self.assertIn(marker, changelog)

        notes = NOTES.read_text(encoding="utf-8")
        for marker in (
            "## Why v0.2 Matters",
            "## Quick Experience",
            "## Packaging",
            "## Safety Boundaries",
            "## Known Limitations",
            "## Upgrading from v0.1.0",
        ):
            self.assertIn(marker, notes)


if __name__ == "__main__":
    unittest.main()
