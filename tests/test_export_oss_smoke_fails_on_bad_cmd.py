import os
import subprocess
import sys
import tempfile
import unittest


class ExportOssSmokeFailsOnBadCmdTest(unittest.TestCase):
    def test_smoke_fail(self):
        out = tempfile.mkdtemp(prefix="oss_smoke_bad_")
        os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        cmd = f'"{sys.executable}" -c "import sys; sys.exit(3)"'
        res = subprocess.run(
            [sys.executable, "tools/release/export_oss.py", "--out", out, "--smoke", "--smoke-cmd", cmd],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("smoke_failed", res.stdout)


if __name__ == "__main__":
    unittest.main()
