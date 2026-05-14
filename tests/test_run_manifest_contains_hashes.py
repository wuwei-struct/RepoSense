import os
import json
import tempfile
import unittest
from reposense.ci import run_ci


class RunManifestContainsHashesTest(unittest.TestCase):
    def test_manifest_exists_and_hashes(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "entrypoints_min"))
        out = tempfile.mkdtemp(prefix="ci_run_manifest_")
        code = run_ci(repo, out, profile="prod_lite")
        self.assertIn(code, (0,2))
        runs = [os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")]
        rd = sorted(runs)[-1]
        rm = os.path.join(rd, "run_manifest.json")
        self.assertTrue(os.path.isfile(rm))
        obj = json.load(open(rm, "r", encoding="utf-8"))
        arts = obj.get("artifacts", [])
        self.assertTrue(any(a.get("path") == "report.json" for a in arts))
        # check hash matches
        rep = os.path.join(rd, "report.json")
        h = __import__("hashlib").sha256(open(rep, "rb").read()).hexdigest()
        self.assertTrue(any(a.get("path") == "report.json" and a.get("sha256") == h for a in arts))


if __name__ == "__main__":
    unittest.main()
