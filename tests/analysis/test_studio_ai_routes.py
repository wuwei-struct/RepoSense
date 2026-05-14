import os
import shutil
import unittest

from reposense.report import build_report_html
from tests.analysis._studio_ai_fixture import build_studio_ai_run_dir


class StudioAIRoutesTest(unittest.TestCase):
    def test_run_page_contains_ai_sections(self):
        rd = build_studio_ai_run_dir(with_ai=True)
        try:
            build_report_html(rd)
            with open(os.path.join(rd, "report.html"), "r", encoding="utf-8") as f:
                html = f.read()
            self.assertIn("id=\"ai-summary\"", html)
            self.assertIn("id=\"ai-risks\"", html)
            self.assertIn("openExplainByPattern", html)
            self.assertIn("openSnippetByRequest", html)
        finally:
            shutil.rmtree(rd, ignore_errors=True)
