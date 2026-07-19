import json
import unittest

from reposense.analysis.authz.route_guard_correlation import (
    build_route_guard_correlation,
)
from tests.analysis._route_decorator_fixture import fixture_repo


class GuardCorrelationRouteDecoratorIntegrationTest(unittest.TestCase):
    def test_guard_correlation_only_uses_canonical_code_routes(self):
        payload, summary, _openapi, nest = build_route_guard_correlation(
            fixture_repo()
        )
        encoded = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("DeleteDateColumn", encoded)
        self.assertFalse(
            any(
                row["file"].endswith("order.entity.ts")
                for row in nest["routes"]
            )
        )
        self.assertEqual(summary["total_code_routes"], 8)


if __name__ == "__main__":
    unittest.main()
