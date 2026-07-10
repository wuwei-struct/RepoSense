import unittest

from reposense.analysis.review.review_schema import VALID_DECISIONS, normalize_human_review_item, normalize_risk_matrix


class RepositoryReviewSchemaTest(unittest.TestCase):
    def test_decision_values(self):
        self.assertEqual(VALID_DECISIONS, {"PASS", "WARN", "REVIEW", "BLOCK"})
        self.assertEqual(normalize_risk_matrix({"decision": "BAD"})["decision"], "REVIEW")
        self.assertEqual(normalize_risk_matrix({"decision": "warn"})["decision"], "WARN")

    def test_human_review_item_required_fields(self):
        item = normalize_human_review_item(
            {
                "path": "svc/order.py",
                "reason": ["DB write found"],
                "required_decision": ["Should this operation be transactional?"],
            }
        )
        self.assertTrue(item["reason"])
        self.assertTrue(item["required_decision"])


if __name__ == "__main__":
    unittest.main()

