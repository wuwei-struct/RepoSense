import os, json, unittest, tempfile, sys, subprocess
from tests.learn._mk_run_dir import mk_run_dir
class ContextPackBuildDirTest(unittest.TestCase):
    def test_pack_build_dir(self):
        rd = mk_run_dir()
        outd = tempfile.mkdtemp(prefix="ctx-out-")
        cmd = [sys.executable, "-m", "reposense", "context", "pack", rd, "--out", outd, "--include-evidence"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        self.assertEqual(res.returncode, 0)
        files = set(os.listdir(outd))
        for need in ["README.md","context_manifest.json","repo_fingerprint.json","snapshot.json","stats.json","checksums.json","warnings.json","artifacts"]:
            self.assertIn(need, files)
        with open(os.path.join(outd,"checksums.json"),"r",encoding="utf-8") as f:
            checks = json.load(f)
        paths = [c["path"] for c in checks]
        # ensure checksums cover README and manifest
        self.assertIn("README.md", paths)
        self.assertIn("context_manifest.json", paths)
