import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class PatternCliTest(unittest.TestCase):
    def test_ai_patterns_cli_json(self):
        rd = tempfile.mkdtemp(prefix="pattern-cli-run-")
        try:
            with open(os.path.join(rd, "report.json"), "w", encoding="utf-8") as f:
                json.dump({"findings": []}, f)
            with open(os.path.join(rd, "event_graph.json"), "w", encoding="utf-8") as f:
                json.dump({"nodes": [], "edges": []}, f)
            cmd = [sys.executable, "-m", "reposense", "ai", "patterns", rd, "--json"]
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(p.returncode, 0)
            obj = json.loads(p.stdout.decode("utf-8"))
            self.assertTrue(obj.get("ok"))
            self.assertTrue(os.path.isfile(os.path.join(rd, "patterns.json")))
            self.assertTrue(os.path.isfile(os.path.join(rd, "pattern_summary.json")))
        finally:
            shutil.rmtree(rd, ignore_errors=True)

