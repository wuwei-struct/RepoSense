import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


class RepoContextPackScriptTest(unittest.TestCase):
    def test_script_generates_pack_dir_and_zip(self):
        repo_root = Path(__file__).resolve().parents[1]
        script = repo_root / "tools" / "gen_repo_context_pack.py"
        self.assertTrue(script.exists(), "gen_repo_context_pack.py should exist")

        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td) / "repo_context_pack"
            cmd = [
                sys.executable,
                str(script),
                "--out",
                str(out_dir),
                "--zip",
                "--max-file-bytes",
                "200000",
                "--exclude",
                ".tmp_test",
            ]
            p = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr or p.stdout)

            self.assertTrue(out_dir.exists())
            self.assertTrue((out_dir / "README.md").exists())
            self.assertTrue((out_dir / "tree.txt").exists())
            self.assertTrue((out_dir / "files_index.json").exists())
            self.assertTrue((out_dir / "checksums.json").exists())
            self.assertTrue((out_dir / "warnings.json").exists())
            self.assertTrue((out_dir / "assets_index.json").exists())
            self.assertTrue(out_dir.with_suffix(".zip").exists())


if __name__ == "__main__":
    unittest.main()
