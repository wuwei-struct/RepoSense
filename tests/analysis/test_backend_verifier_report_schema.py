import shutil
import unittest

from reposense.analysis.reports.backend_verifier_report import generate_backend_verifier_report
from tests.analysis._ai_summary_fixture import build_ai_summary_run_dir


class BackendVerifierReportSchemaTest(unittest.TestCase):
    def test_report_has_fixed_sections(self):
        rd = build_ai_summary_run_dir()
        try:
            rpt = generate_backend_verifier_report(rd)
            self.assertEqual(rpt.get("report_type"), "backend_verifier_report")
            sections = rpt.get("sections") or []
            self.assertEqual(len(sections), 9)
            self.assertIn("API Surface Summary", sections)
            self.assertIn("Limitations", sections)
            self.assertTrue(isinstance(rpt.get("evidence_index"), list))
        finally:
            shutil.rmtree(rd, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

