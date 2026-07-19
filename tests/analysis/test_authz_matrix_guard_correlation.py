import shutil
import unittest

from reposense.analysis.authz.authz_export import export_permission_auditor
from reposense.analysis.authz.authz_matrix_infer import infer_authz_matrix
from tests._tmpdir import make_temp_dir
from tests.analysis._guard_correlation_fixture import fixture_repo


class AuthZMatrixGuardCorrelationTest(unittest.TestCase):
    def test_inferred_matrix_preserves_guard_observations(self):
        run_dir = make_temp_dir(prefix="matrix_guard_correlation_")
        try:
            result = export_permission_auditor(
                run_dir, repo_path=fixture_repo()
            )
            inferred = infer_authz_matrix(
                result["surface"], result["risks"]
            )
            order = inferred["routes"]["POST /orders"]["observed"]
            self.assertEqual(
                order["effective_auth_status"], "protected_global"
            )
            self.assertEqual(order["guard_scope"], "global")
            self.assertGreater(order["guard_correlation_confidence"], 0)
            self.assertEqual(
                order["openapi_security_expectation"], "protected"
            )
            self.assertTrue(
                inferred["routes"]["POST /orders"]["needs_confirmation"]
            )
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
