import os
import subprocess
import sys
import tempfile
import unittest


class ExportOssSnapshotContainsPyprojectTest(unittest.TestCase):
    def test_snapshot_has_pyproject(self):
        out = tempfile.mkdtemp(prefix="oss_pyproj_")
        os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        subprocess.run([sys.executable, "tools/release/export_oss.py", "--out", out], check=True)
        self.assertTrue(os.path.isfile(os.path.join(out, "pyproject.toml")))


if __name__ == "__main__":
    unittest.main()
