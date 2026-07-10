import unittest

from reposense.analysis.health.health_schema import make_health_id, normalize_health_finding


class CodeHealthSchemaTest(unittest.TestCase):
    def test_health_id_is_stable_and_fields_exist(self):
        a = make_health_id("CHD-002", "src/service.ts", 3, "TODO fix", ["debt_comment"])
        b = make_health_id("CHD-002", "src/service.ts", 3, "TODO fix", ["debt_comment"])
        self.assertEqual(a, b)
        item = normalize_health_finding(
            {
                "rule_id": "CHD-002",
                "title": "Debt comment",
                "severity": "medium",
                "status": "confirmed",
                "file": "src/service.ts",
                "line_start": 3,
                "snippet": "// TODO fix",
                "signals": ["debt_comment"],
                "reason": "Debt comment observed.",
            }
        )
        for key in ["health_id", "rule_id", "category", "title", "severity", "status", "file", "line_start", "snippet", "reason", "evidence_refs"]:
            self.assertIn(key, item)
        self.assertIn(item["severity"], {"low", "medium", "high"})
        self.assertIn(item["status"], {"confirmed", "suspected"})


if __name__ == "__main__":
    unittest.main()

