import os
import shutil
import unittest

from reposense.report import build_report_html
from tests.analysis._studio_ai_fixture import build_studio_ai_run_dir


class StudioAIRenderTest(unittest.TestCase):
    def test_render_with_ai(self):
        rd = build_studio_ai_run_dir(with_ai=True)
        try:
            build_report_html(rd)
            with open(os.path.join(rd, "report.html"), "r", encoding="utf-8") as f:
                html = f.read()
            self.assertIn("AI Summary", html)
            self.assertIn("Risks", html)
            self.assertIn("Immediate attention", html)
            self.assertIn("Learn this concept", html)
        finally:
            shutil.rmtree(rd, ignore_errors=True)

    def test_render_empty_states_without_ai(self):
        rd = build_studio_ai_run_dir(with_ai=False)
        try:
            build_report_html(rd)
            with open(os.path.join(rd, "report.html"), "r", encoding="utf-8") as f:
                html = f.read()
            self.assertIn("未生成 AI Summary", html)
            self.assertIn("尚未生成 AI Risks", html)
        finally:
            shutil.rmtree(rd, ignore_errors=True)
