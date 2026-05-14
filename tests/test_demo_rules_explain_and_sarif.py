import os
import json
import tempfile
import unittest
from reposense.scan import run_scan
from reposense.explain import explain_finding
from reposense.sarif import export_sarif


def fixture_path(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "demo_rules", *p))


class DemoRulesExplainAndSarifTest(unittest.TestCase):
    def test_explain_and_sarif(self):
        out = tempfile.mkdtemp(prefix="run_demo2_")
        rd = run_scan(
            fixture_path(),
            out,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "demo_v1")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "demo.json")),
        )
        rep = json.load(open(os.path.join(rd, "report.json"), "r", encoding="utf-8"))
        f0 = rep.get("findings", [])[0]
        fid = f0["fid"]
        ex = explain_finding(rd, fid, as_json=True)
        self.assertIn("concept", ex["summary"])
        self.assertIn("rule_id", ex["summary"])
        # markers/score may be absent for pure text L1, but meta_json should exist; allow presence check
        sarif_path = os.path.join(rd, "exports", "report.sarif.json")
        export_sarif(rd, sarif_path)
        s = json.load(open(sarif_path, "r", encoding="utf-8"))
        self.assertTrue((s.get("runs") or [{}])[0].get("results"))


if __name__ == "__main__":
    unittest.main()
