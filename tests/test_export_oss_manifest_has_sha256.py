import os
import json
import subprocess
import sys
import tempfile
import unittest


class ExportOssManifestHasSha256Test(unittest.TestCase):
    def test_manifest(self):
        out = tempfile.mkdtemp(prefix="oss_mani_")
        os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        subprocess.run([sys.executable, "tools/release/export_oss.py", "--out", out], check=True)
        mp = os.path.join(out, "OSS_SNAPSHOT_MANIFEST.json")
        self.assertTrue(os.path.isfile(mp))
        with open(mp, "r", encoding="utf-8") as f:
            m = json.load(f)
        self.assertTrue(all("sha256" in x for x in m.get("files", [])))


if __name__ == "__main__":
    unittest.main()
