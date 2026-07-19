import json
import os
import shutil
import unittest

from reposense.analysis.review.review_engine import generate_repository_review
from tests._tmpdir import make_temp_dir


class ReviewEvidencePropagationTest(unittest.TestCase):
    def setUp(self):
        self.run_dir = make_temp_dir(prefix="review_evidence_")

    def tearDown(self):
        shutil.rmtree(self.run_dir, ignore_errors=True)

    def test_review_keeps_canonical_line_filters_invalid_and_deduplicates(self):
        valid_ref = {"source_type": "event", "event_id": "db-1", "file": "src/repository.py", "start_line": 12, "end_line": 12}
        risks = {
            "risk_items": [
                {
                    "risk_id": "risk-db-1",
                    "title": "DB write outside transaction",
                    "severity": "high",
                    "status": "confirmed",
                    "pattern_type": "db_write_outside_tx",
                    "evidence_refs": [valid_ref],
                },
                {
                    "risk_id": "risk-db-1",
                    "title": "Duplicate rendering of same risk",
                    "severity": "high",
                    "status": "confirmed",
                    "pattern_type": "db_write_outside_tx",
                    "evidence_refs": [valid_ref],
                },
                {
                    "risk_id": "risk-invalid",
                    "title": "Invalid legacy location",
                    "severity": "high",
                    "status": "confirmed",
                    "pattern_type": "db_write_outside_tx",
                    "evidence_refs": [{"file": "src/repository.py", "start_line": 0, "end_line": 0}],
                },
            ]
        }
        os.makedirs(os.path.join(self.run_dir, "ai_risks"))
        with open(os.path.join(self.run_dir, "ai_risks", "risks.json"), "w", encoding="utf-8") as handle:
            json.dump(risks, handle)
        with open(os.path.join(self.run_dir, "patterns.json"), "w", encoding="utf-8") as handle:
            json.dump({"patterns": []}, handle)

        report = generate_repository_review(self.run_dir)
        items = report["human_review_required"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["evidence_refs"][0]["start_line"], 12)
        self.assertNotIn(1, [ref.get("start_line") for item in items for ref in item.get("evidence_refs", [])])
        self.assertTrue(any("Skipped 1 invalid evidence" in limitation for limitation in report["limitations"]))


if __name__ == "__main__":
    unittest.main()
