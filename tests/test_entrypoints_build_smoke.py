import os
import json
import tempfile
import unittest
from reposense.scan import run_scan


class EntryPointsBuildSmokeTest(unittest.TestCase):
    def test_entrypoints_smoke(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "entrypoints_min"))
        out = tempfile.mkdtemp(prefix="entry_run_")
        rd = run_scan(repo, out, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2")), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json")))
        p = os.path.join(rd, "entrypoints.json")
        self.assertTrue(os.path.isfile(p))
        data = json.load(open(p, "r", encoding="utf-8"))
        eps = data.get("entrypoints", [])
        self.assertGreaterEqual(len(eps), 3)
        kinds = {e.get("kind") for e in eps}
        ok = {"cli", "docker", "ci"} <= kinds or {"cli", "web", "docker"} <= kinds
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()

