import os
import shutil
import unittest

from reposense.report import build_report_html
from tests.analysis._studio_ai_fixture import build_studio_ai_run_dir


def _snip(text, marker, span=400):
    i = text.find(marker)
    if i < 0:
        return ""
    return text[i : i + span]


class StudioAISnapshotsTest(unittest.TestCase):
    def test_snapshot_with_ai(self):
        rd = build_studio_ai_run_dir(with_ai=True)
        try:
            build_report_html(rd)
            with open(os.path.join(rd, "report.html"), "r", encoding="utf-8") as f:
                html = f.read()
            snap = "\n".join(
                [
                    _snip(html, "id=\"ai-summary\""),
                    _snip(html, "id=\"ai-risks\""),
                    _snip(html, "function openExplainByPattern"),
                    _snip(html, "function openSnippetByRequest"),
                ]
            )
            self.assertIn("id=\"ai-summary\"", snap)
            self.assertIn("id=\"ai-risks\"", snap)
            self.assertIn("openExplainByPattern", snap)
            self.assertIn("openSnippetByRequest", snap)
        finally:
            shutil.rmtree(rd, ignore_errors=True)

    def test_snapshot_empty_state(self):
        rd = build_studio_ai_run_dir(with_ai=False)
        try:
            build_report_html(rd)
            with open(os.path.join(rd, "report.html"), "r", encoding="utf-8") as f:
                html = f.read()
            self.assertIn("未生成 AI Summary", html)
            self.assertIn("尚未生成 AI Risks", html)
        finally:
            shutil.rmtree(rd, ignore_errors=True)
