import os
import shutil
import unittest

from reposense.analysis.authz.authz_matrix_loader import load_authz_contract
from tests._tmpdir import make_temp_dir


class AuthZMatrixLoaderTest(unittest.TestCase):
    def test_loads_contract_and_defaults_missing_fields(self):
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "authz_matrix_min", "reposense.authz.yaml"))
        obj = load_authz_contract(path)
        self.assertEqual(obj.get("version"), "authz_matrix_contract_v1")
        self.assertEqual(len(obj.get("routes") or []), 1)
        self.assertEqual((obj["routes"][0]["expected"] or {}).get("auth"), "required")

    def test_invalid_yaml_has_clear_error(self):
        tmp = make_temp_dir(prefix="authz_bad_yaml_")
        try:
            bad = os.path.join(tmp, "reposense.authz.yaml")
            with open(bad, "w", encoding="utf-8") as f:
                f.write("routes: [:\n")
            with self.assertRaisesRegex(ValueError, "invalid authz contract yaml"):
                load_authz_contract(bad)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

