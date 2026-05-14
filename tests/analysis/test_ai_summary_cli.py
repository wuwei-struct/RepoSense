import json
import os
import shutil
import subprocess
import sys
import unittest

from tests.analysis._ai_summary_fixture import build_ai_summary_run_dir


class AISummaryCliTest(unittest.TestCase):
    def test_cli_summary_json_and_markdown(self):
        rd = build_ai_summary_run_dir()
        try:
            cmd = [sys.executable, "-m", "reposense", "ai", "summary", rd, "--json", "--markdown"]
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(p.returncode, 0)
            self.assertTrue(os.path.isfile(os.path.join(rd, "ai_summary.json")))
            self.assertTrue(os.path.isfile(os.path.join(rd, "ai_summary.md")))
            with open(os.path.join(rd, "ai_summary.json"), "r", encoding="utf-8") as f:
                obj = json.load(f)
            self.assertEqual(obj.get("mode"), "facts_only")
        finally:
            shutil.rmtree(rd, ignore_errors=True)
