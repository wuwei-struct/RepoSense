import unittest

from reposense.analysis.authz.authz_scanner import scan_permission_auditor
from tests.analysis._review_context_fixture import build_context_run, fixture_repo


class PublicAuthEntrypointClassificationTest(unittest.TestCase):
    def test_login_register_and_forgot_password_are_public(self):
        surface, _ = scan_permission_auditor(build_context_run(), fixture_repo())
        by_path = {row["path"]: row for row in surface["routes"]}
        for path in ["/auth/login", "/auth/register", "/auth/forgot-password"]:
            self.assertEqual(by_path[path]["intent"], "public_auth_entrypoint")
            self.assertGreaterEqual(by_path[path]["intent_confidence"], 0.8)
            self.assertFalse(by_path[path]["auth_guard_expected"])

    def test_sensitive_conflict_stays_unknown(self):
        surface, _ = scan_permission_auditor(build_context_run(), fixture_repo())
        route = next(row for row in surface["routes"] if row["path"] == "/auth/login/refund")
        self.assertEqual(route["intent"], "unknown")
        self.assertIn("route_intent_conflict", route["intent_limitations"])


if __name__ == "__main__":
    unittest.main()
