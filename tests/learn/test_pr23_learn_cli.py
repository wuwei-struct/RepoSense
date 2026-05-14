import os
import json
import sys
import unittest
import tempfile
import subprocess
from ._mk_run_dir_pr23 import mk_run_dir_pr23


class Pr23LearnCliTest(unittest.TestCase):
    def test_concepts_extract_cases_cli(self):
        rd = mk_run_dir_pr23()
        outd = tempfile.mkdtemp(prefix="pr23-cli-")
        p1 = subprocess.run([sys.executable, "-m", "reposense", "learn", "concepts", "--json"], stdout=subprocess.PIPE)
        self.assertEqual(p1.returncode, 0)
        arr = json.loads(p1.stdout.decode("utf-8"))
        ids = set([(x.get("concept_id") or "").lower() for x in arr])
        self.assertIn("data.transaction_boundary", ids)
        p2 = subprocess.run([sys.executable, "-m", "reposense", "learn", "extract-cases", rd, "--out", outd, "--min-confidence", "0.0", "--json"], stdout=subprocess.PIPE)
        self.assertEqual(p2.returncode, 0)
        obj = json.loads(p2.stdout.decode("utf-8"))
        self.assertTrue(obj.get("ok"))
        p3 = subprocess.run([sys.executable, "-m", "reposense", "learn", "cases", "data.transaction_boundary", "--dir", outd, "--json"], stdout=subprocess.PIPE)
        self.assertEqual(p3.returncode, 0)
        cs = json.loads(p3.stdout.decode("utf-8"))
        self.assertTrue(len(cs) >= 10)
        self.assertTrue(all((c.get("concept_id") == "data.transaction_boundary") for c in cs))
        self.assertTrue(os.path.isfile(os.path.join(outd, "cases_index.json")))


if __name__ == "__main__":
    unittest.main()
