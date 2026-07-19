import unittest

from reposense.analysis.authz.route_guard_correlation import (
    build_route_guard_correlation,
)
from tests.analysis._guard_correlation_fixture import fixture_repo


class PublicGuardBypassCorrelationTest(unittest.TestCase):
    def test_public_bypass_wins_over_global_guard(self):
        payload, _summary, _openapi, _nest = build_route_guard_correlation(
            fixture_repo()
        )
        login = next(
            row
            for row in payload["correlations"]
            if row["method"] == "POST" and row["path"] == "/auth/login"
        )
        self.assertEqual(
            login["effective_auth_status"], "intentional_public_bypass"
        )
        self.assertEqual(login["openapi_security_expectation"], "public")
        self.assertTrue(login["public_bypass_sources"])
        self.assertGreaterEqual(login["confidence"], 0.8)


if __name__ == "__main__":
    unittest.main()
