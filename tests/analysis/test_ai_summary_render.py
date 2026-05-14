import shutil
import unittest

from reposense.analysis.ai.summary_engine import generate_facts_only_summary
from reposense.analysis.ai.summary_render import render_summary_markdown
from tests.analysis._ai_summary_fixture import build_ai_summary_run_dir


class AISummaryRenderTest(unittest.TestCase):
    def test_markdown_stable_sections(self):
        rd = build_ai_summary_run_dir()
        try:
            s = generate_facts_only_summary(rd)
            md = render_summary_markdown(s)
            self.assertIn("# RepoSense AI Summary", md)
            self.assertIn("## 1. 项目概览", md)
            self.assertIn("## 6. 建议优先关注点", md)
            self.assertIn("## 已知局限", md)
        finally:
            shutil.rmtree(rd, ignore_errors=True)

