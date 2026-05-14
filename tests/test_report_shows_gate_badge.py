import os
import json
import tempfile
import unittest
from reposense.report import build_report_html


class ReportShowsGateBadgeTest(unittest.TestCase):
    def test_report_shows_gate_badge(self):
        rd = tempfile.mkdtemp(prefix="gate_badge_")
        with open(os.path.join(rd, "report.json"), "w", encoding="utf-8") as f:
            json.dump({"findings": [], "run_summary": {}}, f)
        with open(os.path.join(rd, "quality_gate.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "warn", "violations": [{"level":"warn","metric":"skipped_ratio","message":"跳过过多"}]}, f)
        build_report_html(rd)
        with open(os.path.join(rd, "report.html"), "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("Gate:", html)
        self.assertIn("WARN", html)


if __name__ == "__main__":
    unittest.main()
