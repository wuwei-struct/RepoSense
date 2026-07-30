import unittest
from pathlib import Path


AUDIT = Path("docs/release/V0_2_0_RELEASE_READINESS_AUDIT.md")
NOTES = Path("docs/release/V0_2_0_RELEASE_NOTES_DRAFT.md")
ALLOWED = {
    "SUPPORTED",
    "SUPPORTED_WITH_LIMITATIONS",
    "NOT_YET_SUPPORTED",
    "DO_NOT_CLAIM",
}


class V020ReleaseClaimsTest(unittest.TestCase):
    def test_claims_matrix_uses_only_allowed_states(self):
        text = AUDIT.read_text(encoding="utf-8")
        rows = []
        for line in text.splitlines():
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[1] in ALLOWED:
                rows.append(cells)
        self.assertGreaterEqual(len(rows), 25)
        self.assertTrue(all(row[1] in ALLOWED for row in rows))

    def test_required_claims_are_classified(self):
        text = AUDIT.read_text(encoding="utf-8")
        for capability in (
            "Repository Review",
            "Human Review Required",
            "Code Health Radar",
            "Permission Auditor",
            "AuthZ Matrix",
            "Spring transaction correlation",
            "TypeORM DB operations",
            "TypeScript transaction correlation",
            "TypeORM alias resolution",
            "Queue / Cache",
            "Queue Retry / Idempotency",
            "OpenAPI / Guard correlation",
            "Route Decorator classification",
            "Cross-language links",
            "Context Pack REVIEW",
            "Studio Artifact Cards",
            "Learn UI",
            "Local AI outputs",
            "Real-repository validation",
            "Packaging / fresh-venv install",
            "Cross-platform packaging",
            "Replace code review",
            "Security guarantee",
            "Automatic repair",
            "Complete business-intent understanding",
        ):
            self.assertIn(f"| {capability} |", text)

    def test_release_notes_do_not_make_prohibited_claims(self):
        text = NOTES.read_text(encoding="utf-8").lower()
        for phrase in (
            "reposense certifies that a repository is safe",
            "reposense proves that a repository is safe",
            "guarantees security",
            "guarantees authorization",
            "replaces code review",
            "automatically repairs",
            "complete business intent",
        ):
            self.assertNotIn(phrase, text)
        self.assertIn("does not certify", text)
        self.assertIn("human review remains required", text)

    def test_boundary_language_is_present(self):
        text = AUDIT.read_text(encoding="utf-8")
        for marker in (
            "OpenAPI security is not implementation proof",
            "producer identity is not consumer idempotency",
            "Spring `SecurityFilterChain` inference is not implemented",
            "CPython 3.11 on Windows AMD64",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
