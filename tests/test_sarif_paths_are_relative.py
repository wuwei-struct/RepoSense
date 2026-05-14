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


def fx_flask_min():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "prod_suite", "python_flask_min"))


class SarifPathsAreRelativeTest(unittest.TestCase):
    def test_paths_are_relative(self):
        out = tempfile.mkdtemp(prefix="sarif_rel_")
        rd = run_scan(fx_flask_min(), out, ruleset_specs_v2(), budget_prod_lite())
        p = os.path.join(rd, "exports", "report.sarif.json")
        export_sarif(rd, p)
        s = json.load(open(p, "r", encoding="utf-8"))
        r = ((s.get("runs") or [{}])[0].get("results") or [])
        for res in r:
            locs = res.get("locations") or []
            if not locs:
                continue
            uri = ((locs[0].get("physicalLocation") or {}).get("artifactLocation") or {}).get("uri", "")
            self.assertTrue(uri and ":" not in uri and not uri.startswith("/"))


if __name__ == "__main__":
    unittest.main()

