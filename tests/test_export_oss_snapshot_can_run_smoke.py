import os
import subprocess
import sys
import tempfile
import unittest


class ExportOssSnapshotCanRunSmokeTest(unittest.TestCase):
    def test_snapshot_has_scripts(self):
        out = tempfile.mkdtemp(prefix="oss_smoke_")
        os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        subprocess.run([sys.executable, "tools/release/export_oss.py", "--out", out], check=True)
        self.assertTrue(os.path.isfile(os.path.join(out, "scripts","demo_run.sh")))
        self.assertTrue(os.path.isfile(os.path.join(out, "scripts","demo_run.ps1")))
        with open(os.path.join(out, "scripts", "demo_run.sh"), "r", encoding="utf-8") as f:
            self.assertIn("reposense ci run", f.read())


if __name__ == "__main__":
    unittest.main()
