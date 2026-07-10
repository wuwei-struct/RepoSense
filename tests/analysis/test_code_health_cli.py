import json
import os
import shutil
import subprocess
import sys
import unittest

from tests._tmpdir import make_temp_dir


class CodeHealthCliTest(unittest.TestCase):
    def test_health_scan_cli_writes_outputs(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "code_health_smoke_min"))
        run_dir = make_temp_dir(prefix="code_health_cli_run_")
        try:
            with open(os.path.join(run_dir, "event_graph.json"), "w", encoding="utf-8") as f:
                json.dump({"nodes": [{"event_id": "e1", "type": "db_op", "meta": {"path": "src/service.ts", "start_line": 3, "db.kind": "db.write"}}]}, f)
            cmd = [sys.executable, "-m", "reposense", "health", "scan", run_dir, "--repo", repo, "--json"]
            res = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(res.returncode, 0, res.stderr + res.stdout)
            for name in ["code_health.json", "code_health_summary.json", "maintainability_risks.json"]:
                self.assertTrue(os.path.isfile(os.path.join(run_dir, name)), name)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

