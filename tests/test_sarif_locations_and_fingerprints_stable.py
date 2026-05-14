import os
import json
import tempfile
import unittest
from reposense.scan import run_scan
from reposense.sarif import export_sarif


def ruleset_specs_v2():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2"))


def budget_prod_lite():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json"))


def fx_fastapi_min():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "prod_suite", "python_fastapi_min"))


class SarifLocationsAndFingerprintsStableTest(unittest.TestCase):
    def test_locations_and_fingerprints_stable(self):
        out = tempfile.mkdtemp(prefix="sarif_fp_")
        rd = run_scan(fx_fastapi_min(), out, ruleset_specs_v2(), budget_prod_lite())
        p1 = os.path.join(rd, "exports", "report.sarif.json")
        p2 = os.path.join(rd, "exports", "report2.sarif.json")
        export_sarif(rd, p1)
        export_sarif(rd, p2)
        s1 = json.load(open(p1, "r", encoding="utf-8"))
        s2 = json.load(open(p2, "r", encoding="utf-8"))
        r1 = ((s1.get("runs") or [{}])[0].get("results") or [])
        r2 = ((s2.get("runs") or [{}])[0].get("results") or [])
        # locations startLine exists
        self.assertTrue(all(((res.get("locations") or [{}])[0].get("physicalLocation") or {}).get("region", {}).get("startLine") for res in r1))
        # fingerprints present and stable across exports
        f1 = set([res.get("fingerprints", {}).get("reposense/v1") for res in r1])
        f2 = set([res.get("fingerprints", {}).get("reposense/v1") for res in r2])
        self.assertEqual(f1, f2)


if __name__ == "__main__":
    unittest.main()

