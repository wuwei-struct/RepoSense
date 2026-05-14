import os, json, unittest, tempfile, sys, subprocess, zipfile
from tests.learn._mk_run_dir import mk_run_dir
class ContextPackZipTest(unittest.TestCase):
    def test_pack_zip(self):
        rd = mk_run_dir()
        outd = tempfile.mkdtemp(prefix="ctx-out-")
        cmd = [sys.executable, "-m", "reposense", "context", "pack", rd, "--out", outd, "--zip"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        self.assertEqual(res.returncode, 0)
        zp = outd + ".zip"
        self.assertTrue(os.path.isfile(zp))
        with zipfile.ZipFile(zp, "r") as zf:
            names = zf.namelist()
        self.assertTrue(any(n.endswith("README.md") for n in names))
        self.assertTrue(any(n.endswith("checksums.json") for n in names))
