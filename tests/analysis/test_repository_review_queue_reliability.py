import unittest

from reposense.analysis.ai.risks_export import export_ai_risks
from reposense.analysis.review.review_engine import generate_repository_review
from tests.analysis.test_queue_reliability_schema import (
    build_queue_reliability_run,
)


class RepositoryReviewQueueReliabilityTest(unittest.TestCase):
    def test_review_summary_and_human_items(self):
        run_dir = build_queue_reliability_run()
        export_ai_risks(
            run_dir,
            max_auto_drilldowns=0,
            severity_threshold="medium",
        )
        review = generate_repository_review(run_dir)
        section = review["messaging_reliability_review"]
        self.assertEqual(section["status"], "enabled")
        self.assertEqual(section["explicit_retries"], 7)
        self.assertEqual(section["actionable_suspected_risks"], 5)
        human = review.get("human_review_required") or []
        queue_items = [
            item
            for item in human
            if any(
                "idempotency evidence not observed" in reason
                for reason in item.get("reason") or []
            )
        ]
        self.assertEqual(len(queue_items), 5)
        keys = {
            (
                tuple(item.get("related_patterns") or []),
                tuple(
                    (
                        ref.get("file"),
                        ref.get("start_line"),
                        ref.get("end_line"),
                    )
                    for ref in item.get("evidence_refs") or []
                ),
            )
            for item in queue_items
        }
        self.assertEqual(len(keys), 5)


if __name__ == "__main__":
    unittest.main()
