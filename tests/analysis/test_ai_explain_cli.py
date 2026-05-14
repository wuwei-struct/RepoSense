import os
import shutil
import subprocess
import sys
import unittest

from tests.analysis._drilldown_fixture import build_drilldown_run_dir


class AIExplainCliTest(unittest.TestCase):
    def test_pattern_finding_event_cli(self):
        rd = build_drilldown_run_dir()
        try:
            cmds = [
                [sys.executable, "-m", "reposense", "ai", "explain", rd, "--pattern-id", "pat-1", "--json", "--markdown"],
                [sys.executable, "-m", "reposense", "ai", "explain", rd, "--finding-id", "f-1", "--json"],
                [sys.executable, "-m", "reposense", "ai", "explain", rd, "--event-id", "e-1", "--json"],
            ]
            for cmd in cmds:
                p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual(p.returncode, 0, msg=p.stderr.decode("utf-8", errors="ignore"))
            self.assertTrue(os.path.isdir(os.path.join(rd, "ai_explain")))
        finally:
            shutil.rmtree(rd, ignore_errors=True)

