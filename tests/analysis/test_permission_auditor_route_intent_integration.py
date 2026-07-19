import unittest

from reposense.analysis.authz.authz_scanner import scan_permission_auditor
from tests.analysis._review_context_fixture import build_context_run, fixture_repo


class PermissionAuditorRouteIntentIntegrationTest(unittest.TestCase):
    def test_public_auth_missing_guard_is_not_primary_risk(self):
        _surface, payload = scan_permission_auditor(build_context_run(), fixture_repo())
        risks = payload["risks"]
        primary = [
            risk
            for risk in risks
            if risk["rule_id"] in {"AUTHZ-001", "AUTHZ-002"}
        ]
        primary_paths = {risk["route"]["path"] for risk in primary}
        self.assertNotIn("/auth/login", primary_paths)
        self.assertNotIn("/auth/register", primary_paths)
        self.assertIn("/auth/logout", primary_paths)
        self.assertIn("/orders", primary_paths)

        login_test_gap = next(
            risk
            for risk in risks
            if risk["rule_id"] == "AUTHZ-005" and risk["route"]["path"] == "/auth/login"
        )
        self.assertEqual(login_test_gap["severity"], "low")
        self.assertFalse(login_test_gap["suggested_human_review"])


if __name__ == "__main__":
    unittest.main()
