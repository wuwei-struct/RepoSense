import os
import json
import tempfile
import unittest
from reposense.scan import run_scan


class ProdBudgetHardLimitsTest(unittest.TestCase):
    def test_large_and_binary_files_skipped_with_reasons(self):
        repo = tempfile.mkdtemp(prefix="repo_big_")
        big_path = os.path.join(repo, "big.txt")
        with open(big_path, "wb") as f:
            f.write(b"a" * (3 * 1024 * 1024))
        bin_path = os.path.join(repo, "bin.dat")
        with open(bin_path, "wb") as f:
            f.write(b"\x00\x01\x02" * 4096)
        out = tempfile.mkdtemp(prefix="run_out_")
        rd = run_scan(
            repo,
            out,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json")),
        )
        cov = json.load(open(os.path.join(rd, "coverage.json"), "r", encoding="utf-8"))
        skipped = (cov.get("walk") or {}).get("skipped") or {}
        self.assertTrue(skipped.get("too_large", 0) >= 1)
        self.assertTrue(skipped.get("binary", 0) >= 1)


if __name__ == "__main__":
    unittest.main()

