import os, json, unittest, tempfile, sys, subprocess
from tests.learn._mk_run_dir import mk_run_dir
class ContextPackDeterministicOrderTest(unittest.TestCase):
    def test_snapshot_order_stable(self):
        rd = mk_run_dir()
        out1 = tempfile.mkdtemp(prefix="ctx-out-")
        out2 = tempfile.mkdtemp(prefix="ctx-out-")
        subprocess.run([sys.executable, "-m", "reposense", "context", "pack", rd, "--out", out1])
        subprocess.run([sys.executable, "-m", "reposense", "context", "pack", rd, "--out", out2])
        s1 = json.load(open(os.path.join(out1, "snapshot.json"), "r", encoding="utf-8"))
        s2 = json.load(open(os.path.join(out2, "snapshot.json"), "r", encoding="utf-8"))
        self.assertEqual(s1.get("findings"), s2.get("findings"))
        self.assertEqual(s1.get("events"), s2.get("events"))
