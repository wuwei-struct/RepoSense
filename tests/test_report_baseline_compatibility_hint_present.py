import os
import json
import tempfile
import unittest
from reposense.report import build_report_html


class ReportBaselineCompatibilityHintPresentTest(unittest.TestCase):
    def test_incompatible_hint_shown(self):
        rd = tempfile.mkdtemp(prefix="report_compat_hint_")
        json.dump({"findings": [], "run_summary": {}}, open(os.path.join(rd, "report.json"), "w", encoding="utf-8"))
        json.dump({"baseline_used": True, "baseline_compatible": False, "regressions": {"total": 0}}, open(os.path.join(rd, "quality_gate.json"), "w", encoding="utf-8"))
        json.dump({"schema_version":1,"compatible":False,"stats":{},"added":[],"removed":[],"severity_changed":[]}, open(os.path.join(rd, "baseline_diff.json"), "w", encoding="utf-8"))
        build_report_html(rd)
        html = open(os.path.join(rd, "report.html"), "r", encoding="utf-8").read()
        self.assertIn("Baseline incompatible", html)


if __name__ == "__main__":
    unittest.main()
