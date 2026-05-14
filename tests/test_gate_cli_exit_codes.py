import os
import subprocess
import tempfile
import json
import sys
import unittest


class GateCliExitCodesTest(unittest.TestCase):
    def _mk_run(self, fail=False):
        rd = tempfile.mkdtemp(prefix="gate_cli_")
        with open(os.path.join(rd, "report.json"), "w", encoding="utf-8") as f:
            json.dump({"run_summary": {"artifacts_missing": (["x"] if fail else []), "truncation": {"budget_cut": fail, "findings_truncated": False, "events_truncated": False}, "scanned_files": 5}}, f)
        with open(os.path.join(rd, "coverage.json"), "w", encoding="utf-8") as f:
            json.dump({"walk": {"included_files": 5, "skipped": {}}}, f)
        with open(os.path.join(rd, "api_surface.json"), "w", encoding="utf-8") as f:
            json.dump({"mismatches": {}}, f)
        return rd

    def test_cli_exit_codes(self):
        rd_ok = self._mk_run(fail=False)
        rd_fail = self._mk_run(fail=True)
        gate_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "gates", "prod_lite.json"))
        p_ok = subprocess.run([sys.executable, "-m", "reposense", "gate", rd_ok, "--gate", gate_path], capture_output=True, text=True)
        self.assertEqual(p_ok.returncode, 0)
        p_fail = subprocess.run([sys.executable, "-m", "reposense", "gate", rd_fail, "--gate", gate_path], capture_output=True, text=True)
        self.assertEqual(p_fail.returncode, 2)


if __name__ == "__main__":
    unittest.main()
