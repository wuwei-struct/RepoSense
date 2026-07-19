import unittest

from reposense.analysis.authz.route_guard_correlation import (
    build_route_guard_correlation,
)
from tests.analysis._guard_correlation_fixture import fixture_repo


class OpenAPIRouteGuardCorrelationTest(unittest.TestCase):
    def test_exact_template_openapi_only_and_ambiguous(self):
        payload, summary, _openapi, _nest = build_route_guard_correlation(
            fixture_repo()
        )
        rows = payload["correlations"]
        order = next(
            row for row in rows
            if row["method"] == "POST" and row["path"] == "/orders"
        )
        user = next(
            row for row in rows
            if row["method"] == "GET" and row["path"] == "/users/{id}"
        )
        billing = next(
            row for row in rows
            if row["method"] == "POST" and row["path"] == "/billing/export"
        )
        ambiguous = next(
            row for row in rows
            if row["method"] == "GET" and row["path"] == "/ambiguous"
        )
        self.assertEqual(order["match_status"], "exact_match")
        self.assertEqual(user["match_status"], "template_match")
        self.assertEqual(billing["match_status"], "openapi_only")
        self.assertEqual(ambiguous["match_status"], "ambiguous")
        self.assertGreater(summary["exact_matches"], 0)
        self.assertGreater(summary["template_matches"], 0)
        self.assertGreater(summary["openapi_only_routes"], 0)


if __name__ == "__main__":
    unittest.main()
