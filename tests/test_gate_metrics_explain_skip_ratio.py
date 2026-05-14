import os
import json
import tempfile
import unittest
from reposense.quality_gate import collect_metrics


class GateMetricsExplainSkipRatioTest(unittest.TestCase):
    def test_metrics_include_skip_reasons(self):
        rd = tempfile.mkdtemp(prefix="gate_metrics_")
        cov = {
            "walk": {
                "included_files": 5,
                "skipped": {"ignored_dir": 10, "ignored_ext": 3, "too_large": 2}
            },
            "warnings": []
        }
        rep = {"run_summary": {"scanned_files": 5, "skipped_files_by_reason": [["ignored_dir", 10], ["ignored_ext", 3], ["too_large", 2]]}}
        with open(os.path.join(rd, "coverage.json"), "w", encoding="utf-8") as f:
            json.dump(cov, f)
        with open(os.path.join(rd, "report.json"), "w", encoding="utf-8") as f:
            json.dump(rep, f)
        m = collect_metrics(rd)
        self.assertIn("skipped_files_by_reason_top", m)
        self.assertGreaterEqual(len(m.get("skipped_files_by_reason_top", [])), 1)
        self.assertIn("skipped_files_count", m)
        self.assertIn("scanned_files_count", m)


if __name__ == "__main__":
    unittest.main()
