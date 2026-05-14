import os
import shutil
import tempfile
import unittest
from tools.release.export_oss import main as export_main


class ExportOssAllowlistOnlyTest(unittest.TestCase):
    def test_no_specs_v2(self):
        out = tempfile.mkdtemp(prefix="oss_export_")
        os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        os.system(f"python tools/release/export_oss.py --out \"{out}\"")
        self.assertFalse(os.path.exists(os.path.join(out, "rulesets","specs_v2")))
        self.assertFalse(os.path.exists(os.path.join(out, "enterprise")))


if __name__ == "__main__":
    unittest.main()
