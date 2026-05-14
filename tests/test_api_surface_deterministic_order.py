import os
import json
import tempfile
import unittest
from reposense.scan import run_scan


class ApiSurfaceDeterministicOrderTest(unittest.TestCase):
    def test_api_surface_order_stable(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "api_surface_mix_min"))
        out1 = tempfile.mkdtemp(prefix="api_surf_run1_")
        out2 = tempfile.mkdtemp(prefix="api_surf_run2_")
        r1 = run_scan(repo, out1, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2")), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json")))
        r2 = run_scan(repo, out2, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2")), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json")))
        d1 = json.load(open(os.path.join(r1, "api_surface.json"), "r", encoding="utf-8"))
        d2 = json.load(open(os.path.join(r2, "api_surface.json"), "r", encoding="utf-8"))
        self.assertEqual(d1.get("endpoints", []), d2.get("endpoints", []))
        self.assertEqual(d1.get("mismatches", {}), d2.get("mismatches", {}))


if __name__ == "__main__":
    unittest.main()

