import unittest

from reposense.analysis.authz.authz_matrix_schema import normalize_diff, stable_matrix_id


class AuthZMatrixSchemaTest(unittest.TestCase):
    def test_diff_id_and_fields(self):
        self.assertEqual(stable_matrix_id("AUTHZ-MATRIX-001", "POST", "/x"), stable_matrix_id("AUTHZ-MATRIX-001", "POST", "/x"))
        d = normalize_diff({"rule_id": "AUTHZ-MATRIX-001", "route": {"method": "post", "path": "/x"}, "missing": ["auth"], "severity": "high", "status": "confirmed"})
        self.assertIn("diff_id", d)
        self.assertEqual(d["route"]["method"], "POST")
        self.assertIn(d["severity"], {"low", "medium", "high"})
        self.assertIn(d["status"], {"confirmed", "suspected"})


if __name__ == "__main__":
    unittest.main()

