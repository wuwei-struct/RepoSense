import os
import json
import tempfile
import unittest
from reposense.scan import run_scan
from reposense.sarif import export_sarif


def ruleset_demo():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "demo_v1"))


def budget_demo():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "demo.json"))


def fx_demo_repo():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "demo_rules"))


class SarifRulesMetadataPresentTest(unittest.TestCase):
    def test_rules_metadata_present(self):
        out = tempfile.mkdtemp(prefix="sarif_meta_")
        rd = run_scan(fx_demo_repo(), out, ruleset_demo(), budget_demo())
        sarif_path = os.path.join(rd, "exports", "report.sarif.json")
        export_sarif(rd, sarif_path)
        s = json.load(open(sarif_path, "r", encoding="utf-8"))
        rules = ((s.get("runs") or [{}])[0].get("tool") or {}).get("driver", {}).get("rules", [])
        self.assertTrue(len(rules) > 0)
        r0 = rules[0]
        self.assertIn("shortDescription", r0)
        self.assertIn("properties", r0)
        self.assertIn("concept", r0.get("properties", {}))


if __name__ == "__main__":
    unittest.main()

