import unittest

from reposense.analysis.authz.authz_scanner import scan_permission_auditor
from tests.analysis._review_context_fixture import build_context_run, fixture_repo


class ProtectedAuthOperationClassificationTest(unittest.TestCase):
    def test_logout_change_password_and_delete_account_remain_protected(self):
        surface, _ = scan_permission_auditor(build_context_run(), fixture_repo())
        by_path = {row["path"]: row for row in surface["routes"]}
        for path in ["/auth/logout", "/auth/change-password", "/auth/account"]:
            self.assertEqual(by_path[path]["intent"], "protected_auth_operation")
            self.assertTrue(by_path[path]["auth_guard_expected"])

    def test_business_write_is_not_public_auth(self):
        surface, _ = scan_permission_auditor(build_context_run(), fixture_repo())
        route = next(row for row in surface["routes"] if row["path"] == "/orders")
        self.assertNotEqual(route["intent"], "public_auth_entrypoint")


if __name__ == "__main__":
    unittest.main()
