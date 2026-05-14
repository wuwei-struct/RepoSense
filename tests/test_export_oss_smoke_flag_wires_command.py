import os
import subprocess
import sys
import tempfile
import unittest


class ExportOssSmokeFlagWiresCommandTest(unittest.TestCase):
    def test_smoke_cmd_runs(self):
        out = tempfile.mkdtemp(prefix="oss_smoke_wire_")
        os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        cmd = f'"{sys.executable}" -c "print(1)"'
        res = subprocess.run(
            [sys.executable, "tools/release/export_oss.py", "--out", out, "--smoke", "--smoke-cmd", cmd],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("smoke_failed", res.stdout)


if __name__ == "__main__":
    unittest.main()
