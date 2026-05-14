import os
import json
import tempfile
import unittest
from reposense.scan import run_scan


class ApiSurfaceBuildSmokeTest(unittest.TestCase):
    def test_api_surface_smoke(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "api_surface_mix_min"))
        out = tempfile.mkdtemp(prefix="api_surf_run_")
        rd = run_scan(repo, out, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2")), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json")))
        p = os.path.join(rd, "api_surface.json")
        self.assertTrue(os.path.isfile(p))
        data = json.load(open(p, "r", encoding="utf-8"))
        self.assertGreaterEqual(len(data.get("endpoints", [])), 2)
        mm = data.get("mismatches", {})
        ok = (len(mm.get("missing_in_spec", [])) >= 1) or (len(mm.get("missing_in_code", [])) >= 1)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()

