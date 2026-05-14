import shutil
import unittest

from reposense.analysis.reports.backend_verifier_report import (
    generate_backend_verifier_report,
    render_backend_verifier_markdown,
)
from tests.analysis._ai_summary_fixture import build_ai_summary_run_dir


class BackendVerifierReportRenderTest(unittest.TestCase):
    def test_markdown_has_nine_sections(self):
        rd = build_ai_summary_run_dir()
        try:
            rpt = generate_backend_verifier_report(rd)
            md = render_backend_verifier_markdown(rpt)
            self.assertIn("# RepoSense Backend Verifier Report", md)
            self.assertIn("## 1. API Surface Summary", md)
            self.assertIn("## 2. Backend Events Summary", md)
            self.assertIn("## 3. Transaction Signals", md)
            self.assertIn("## 4. Queue Dispatch Signals", md)
            self.assertIn("## 5. Cache Operation Signals", md)
            self.assertIn("## 6. Side-effect Map", md)
            self.assertIn("## 7. High-risk Findings", md)
            self.assertIn("## 8. Evidence Index", md)
            self.assertIn("## 9. Limitations", md)
        finally:
            shutil.rmtree(rd, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

