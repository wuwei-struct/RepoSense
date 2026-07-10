import unittest

from reposense.analysis.authz.authz_schema import normalize_risk, normalize_route, stable_id


class PermissionAuditorSchemaTest(unittest.TestCase):
    def test_surface_and_risk_required_fields(self):
        self.assertEqual(stable_id("authz", "AUTHZ-001", "POST", "/x"), stable_id("authz", "AUTHZ-001", "POST", "/x"))
        route = normalize_route({"method": "post", "path": "/api/orders", "file": "src/server.ts", "line_start": 3, "write_like": True})
        self.assertIn("surface_id", route)
        self.assertEqual(route["method"], "POST")
        risk = normalize_risk({"rule_id": "AUTHZ-001", "title": "Public write endpoint", "severity": "high", "status": "confirmed", "route": route, "file": "src/server.ts", "line_start": 3})
        for key in ["risk_id", "rule_id", "category", "title", "severity", "status", "route", "file", "line_start", "evidence_refs"]:
            self.assertIn(key, risk)
        self.assertIn(risk["severity"], {"low", "medium", "high"})
        self.assertIn(risk["status"], {"confirmed", "suspected"})


if __name__ == "__main__":
    unittest.main()

