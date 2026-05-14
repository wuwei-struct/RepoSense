import os
import json
import tempfile
import unittest
from reposense.report import build_report_html


class ReportBaselineDiffCardPresentTest(unittest.TestCase):
    def test_report_has_baseline_card(self):
        rd = tempfile.mkdtemp(prefix="report_base_card_")
        with open(os.path.join(rd, "report.json"), "w", encoding="utf-8") as f:
            json.dump({"findings": [], "run_summary": {}}, f)
        with open(os.path.join(rd, "quality_gate.json"), "w", encoding="utf-8") as f:
            json.dump({"baseline_used": True, "regressions": {"added_error":1,"added_warning":0,"severity_upgrades":0,"total":1}, "regression_samples_top":[{"ruleId":"r","concept":"c","path":"p.py","startLine":1,"severity":"error"}], "baseline_paths":{"baseline_in":"baseline_in.json","diff_json":"baseline_diff.json"}}, f)
        with open(os.path.join(rd, "baseline_diff.json"), "w", encoding="utf-8") as f:
            json.dump({"schema_version":1,"stats":{"added_error":1},"added":[{"ruleId":"r"}],"removed":[],"severity_changed":[]}, f)
        build_report_html(rd)
        html = open(os.path.join(rd, "report.html"), "r", encoding="utf-8").read()
        self.assertIn("Baseline & Diff", html)
        self.assertIn("+E", html)
        self.assertIn("baseline_diff.json", html)


if __name__ == "__main__":
    unittest.main()
