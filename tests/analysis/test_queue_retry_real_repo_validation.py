import json
import tempfile
import unittest
from pathlib import Path

from tests.analysis.test_queue_reliability_schema import (
    build_queue_reliability_run,
    fixture_repo,
)
from tools.validation.queue_retry_idempotency_validation import (
    write_validation,
)


class QueueRetryRealRepoValidationTest(unittest.TestCase):
    def test_validation_and_triage_are_evidence_backed_unreviewed(self):
        run_dir = build_queue_reliability_run()
        with tempfile.TemporaryDirectory(
            dir=".tmp_test_runs/temp"
        ) as case_dir:
            payload = write_validation(
                run_dir,
                fixture_repo(),
                case_id="synthetic",
                commit_sha="fixture",
                case_dir=case_dir,
            )
            summary = payload["summary"]
            self.assertEqual(summary["matched_channels"], 9)
            self.assertEqual(summary["evidence_errors"], 0)
            triage = Path(case_dir) / (
                "queue_retry_idempotency_triage_template.json"
            )
            triage_payload = json.loads(triage.read_text(encoding="utf-8"))
            self.assertTrue(triage_payload["items"])
            self.assertTrue(
                all(
                    item["triage_status"] == "unreviewed"
                    for item in triage_payload["items"]
                )
            )


if __name__ == "__main__":
    unittest.main()
