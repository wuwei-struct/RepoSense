import unittest

from reposense.analysis.authz.route_guard_correlation import (
    build_route_guard_correlation,
)
from tests.analysis._guard_correlation_fixture import fixture_repo


class NestJSGlobalGuardExtractionTest(unittest.TestCase):
    def test_app_guard_protects_ordinary_route(self):
        payload, summary, _openapi, nest = build_route_guard_correlation(
            fixture_repo()
        )
        guard_names = {
            row["guard_name"] for row in nest["global_guards"]
        }
        self.assertIn("JwtAuthGuard", guard_names)
        self.assertIn("SecondaryAuthGuard()", guard_names)
        order = next(
            row
            for row in payload["correlations"]
            if row["method"] == "POST" and row["path"] == "/orders"
        )
        self.assertEqual(order["effective_auth_status"], "protected_global")
        self.assertGreater(summary["protected_global"], 0)


if __name__ == "__main__":
    unittest.main()
