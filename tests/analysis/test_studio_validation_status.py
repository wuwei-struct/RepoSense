import json
import os
import tempfile
import unittest

from reposense.studio.run_summary import build_run_summary


class StudioValidationStatusTest(unittest.TestCase):
    def test_validation_statuses_and_gate_reasons(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "validation.json"), "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "ready_for_manual_calibration": False,
                        "evidence_integrity": {"passed": False, "checked": 8, "errors": [{"code": "EVIDENCE_LINE_START_INVALID"}]},
                        "strict_verification": {"passed": False},
                    },
                    handle,
                )
            with open(os.path.join(td, "quality_gate.json"), "w", encoding="utf-8") as handle:
                json.dump({"status": "warn", "violations": [{"hint": "check truncation"}]}, handle)
            summary = build_run_summary(td)
            self.assertEqual(summary["evidence_integrity"], {"status": "fail", "checked": 8, "errors": 1})
            self.assertEqual(summary["strict_verify"]["status"], "fail")
            self.assertEqual(summary["quality_gate"], {"status": "warn", "reasons": ["check truncation"]})
            self.assertEqual(summary["validation"]["status"], "needs_review")

    def test_missing_validation_is_not_presented_as_pass(self):
        with tempfile.TemporaryDirectory() as td:
            summary = build_run_summary(td)
            self.assertEqual(summary["evidence_integrity"]["status"], "not_available")
            self.assertEqual(summary["strict_verify"]["status"], "not_available")
            self.assertEqual(summary["validation"]["status"], "not_available")


if __name__ == "__main__":
    unittest.main()
