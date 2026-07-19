import unittest

from reposense.analysis.authz.guard_extractor import extract_nestjs_guards
from tests.analysis._guard_correlation_fixture import fixture_repo


class NestJSMethodControllerGuardExtractionTest(unittest.TestCase):
    def test_method_and_controller_guards(self):
        surface = extract_nestjs_guards(fixture_repo())
        routes = {
            (row["method"], row["path"]): row for row in surface["routes"]
        }
        self.assertTrue(routes[("GET", "/account")]["controller_guards"])
        method_guards = routes[("DELETE", "/users/{id}")]["method_guards"]
        self.assertEqual(method_guards[0]["guard_type"], "role")
        self.assertGreater(method_guards[0]["line_start"], 0)


if __name__ == "__main__":
    unittest.main()
