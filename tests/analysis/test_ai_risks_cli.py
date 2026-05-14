import os
import shutil
import subprocess
import sys
import unittest

from tests.analysis._drilldown_fixture import build_drilldown_run_dir


class AIRisksCliTest(unittest.TestCase):
    def test_cli_json_markdown(self):
        rd = build_drilldown_run_dir()
        try:
            cmd = [sys.executable, "-m", "reposense", "ai", "risks", rd, "--json", "--markdown"]
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(p.returncode, 0, msg=p.stderr.decode("utf-8", errors="ignore"))
            self.assertTrue(os.path.isfile(os.path.join(rd, "ai_risks", "risks.json")))
            self.assertTrue(os.path.isfile(os.path.join(rd, "ai_risks", "risks.md")))
        finally:
            shutil.rmtree(rd, ignore_errors=True)

