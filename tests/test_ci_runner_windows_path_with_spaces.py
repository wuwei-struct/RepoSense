import os
import json
import tempfile
import shutil
import subprocess
import sys
import unittest


class CiRunnerWindowsPathWithSpacesTest(unittest.TestCase):
    def test_repo_path_with_spaces(self):
        base = tempfile.mkdtemp(prefix="repo with spaces ")
        src = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "entrypoints_min"))
        # copy fixture repo into base
        for root, dirs, files in os.walk(src):
            rel = os.path.relpath(root, src)
            dst_root = os.path.join(base, rel) if rel != "." else base
            os.makedirs(dst_root, exist_ok=True)
            for f in files:
                shutil.copyfile(os.path.join(root, f), os.path.join(dst_root, f))
        out = tempfile.mkdtemp(prefix="ci_run_out_space_")
        p = subprocess.run([sys.executable, "-m", "reposense", "ci", "run", "--repo", base, "--out", out], capture_output=True, text=True)
        self.assertIn(p.returncode, (0,2))
        runs = [os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")]
        self.assertTrue(len(runs) >= 1)


if __name__ == "__main__":
    unittest.main()
