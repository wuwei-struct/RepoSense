import shutil
import unittest

from reposense.analysis.authz.authz_scanner import scan_permission_auditor
from tests._tmpdir import make_temp_dir
from tests.analysis._guard_correlation_fixture import fixture_repo


class PermissionAuditorGuardCorrelationTest(unittest.TestCase):
    def test_effective_guard_calibrates_permission_risks(self):
        run_dir = make_temp_dir(prefix="permission_guard_correlation_")
        try:
            surface, payload = scan_permission_auditor(
                run_dir, fixture_repo()
            )
            risks = payload["risks"]
            routes = {
                (row["method"], row["path"]): row
                for row in surface["routes"]
            }
            self.assertEqual(
                routes[("POST", "/orders")]["effective_auth_status"],
                "protected_global",
            )
            order_missing_auth = [
                row
                for row in risks
                if (row.get("route") or {}).get("path") == "/orders"
                and row.get("rule_id") in {"AUTHZ-001", "AUTHZ-002"}
            ]
            self.assertEqual(order_missing_auth, [])
            admin_role = [
                row
                for row in risks
                if (row.get("route") or {}).get("path") == "/admin/users"
                and row.get("rule_id") == "AUTHZ-003"
            ]
            self.assertTrue(admin_role)
            login_missing_auth = [
                row
                for row in risks
                if (row.get("route") or {}).get("path") == "/auth/login"
                and row.get("rule_id") in {"AUTHZ-001", "AUTHZ-002"}
            ]
            self.assertEqual(login_missing_auth, [])
            self.assertIn(
                routes[("DELETE", "/users/{id}")][
                    "effective_role_status"
                ],
                {"role_guard_observed", "permission_guard_observed"},
            )
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
