import unittest

from reposense.analysis.health.health_scanner import scan_code_health
from reposense.analysis.health.health_summary import maintainability_risks_from_findings
from tests.analysis._review_context_fixture import build_context_run, fixture_repo


class CodeHealthFileContextIntegrationTest(unittest.TestCase):
    def test_non_production_test_gaps_stay_raw_but_leave_primary_risks(self):
        findings = scan_code_health(build_context_run(), fixture_repo())
        raw_gap_files = {
            row["file"]
            for row in findings
            if row["rule_id"] == "CHD-005"
        }
        for path in [
            "src/generated/client.ts",
            "src/database/seeds/demo.seed.ts",
            "src/templates/service.template.ts",
        ]:
            self.assertIn(path, raw_gap_files)
            finding = next(
                row
                for row in findings
                if row["rule_id"] == "CHD-005" and row["file"] == path
            )
            self.assertEqual(
                finding["metadata"]["review_modifier"],
                "exclude_from_primary_review",
            )

        risks = maintainability_risks_from_findings(findings)["risks"]
        risk_files = {row["file"] for row in risks}
        self.assertNotIn("src/generated/client.ts", risk_files)
        self.assertNotIn("src/database/seeds/demo.seed.ts", risk_files)
        self.assertNotIn("src/templates/service.template.ts", risk_files)
        self.assertIn("src/services/order.service.ts", risk_files)
        self.assertTrue(
            any(
                row["rule_id"] == "CHD-004"
                and row["file"] == "src/services/order.service.ts"
                for row in risks
            )
        )


if __name__ == "__main__":
    unittest.main()
