import unittest

from reposense.analysis.authz.guard_correlation_schema import (
    normalize_correlation,
)


class GuardCorrelationSchemaTest(unittest.TestCase):
    def test_statuses_and_stable_id(self):
        row = {
            "method": "POST",
            "path": "/orders",
            "match_status": "exact_match",
            "effective_auth_status": "protected_global",
            "effective_role_status": "no_role_guard_observed",
        }
        first = normalize_correlation(row)
        second = normalize_correlation(row)
        self.assertEqual(first["correlation_id"], second["correlation_id"])
        self.assertEqual(first["match_status"], "exact_match")
        self.assertEqual(first["effective_auth_status"], "protected_global")

    def test_invalid_statuses_degrade_conservatively(self):
        row = normalize_correlation(
            {
                "match_status": "invented",
                "effective_auth_status": "safe",
                "effective_role_status": "proven",
            }
        )
        self.assertEqual(row["match_status"], "ambiguous")
        self.assertEqual(row["effective_auth_status"], "unknown")
        self.assertEqual(row["effective_role_status"], "unknown")


if __name__ == "__main__":
    unittest.main()
