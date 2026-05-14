import json
import os
import shutil
import subprocess
import sys
import unittest

from tests.analysis._drilldown_fixture import build_drilldown_run_dir


class AIDrilldownCliTest(unittest.TestCase):
    def test_pattern_finding_event_entrypoints(self):
        rd = build_drilldown_run_dir()
        try:
            cmds = [
                [sys.executable, "-m", "reposense", "ai", "drilldown", rd, "--pattern-id", "pat-1", "--json", "--markdown"],
                [sys.executable, "-m", "reposense", "ai", "drilldown", rd, "--finding-id", "f-1", "--json"],
                [sys.executable, "-m", "reposense", "ai", "drilldown", rd, "--event-id", "e-1", "--json"],
            ]
            for cmd in cmds:
                p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual(p.returncode, 0, msg=p.stderr.decode("utf-8", errors="ignore"))
            dd = os.path.join(rd, "ai_drilldown")
            self.assertTrue(os.path.isdir(dd))
            any_json = False
            for root, _, files in os.walk(dd):
                if "snippet_pack.json" in files and "snippet_pack.md" in files:
                    any_json = True
                    with open(os.path.join(root, "snippet_pack.json"), "r", encoding="utf-8") as f:
                        obj = json.load(f)
                    self.assertEqual(obj.get("source_mode"), "facts_first_drilldown")
            self.assertTrue(any_json)
        finally:
            shutil.rmtree(rd, ignore_errors=True)
