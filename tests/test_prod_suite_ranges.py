import os
import json
import tempfile
import unittest
from reposense.scan import run_scan


class ProdSuiteRangesTest(unittest.TestCase):
    def test_prod_suite_ranges(self):
        suite_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "prod_suite"))
        ruleset = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2"))
        budget = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json"))
        for nm in sorted(os.listdir(suite_root)):
            repo = os.path.join(suite_root, nm)
            if not os.path.isdir(repo):
                continue
            exp_path = os.path.join(repo, "expected_ranges.json")
            if not os.path.exists(exp_path):
                continue
            with open(exp_path, "r", encoding="utf-8") as f:
                expected = json.load(f)
            out = tempfile.mkdtemp(prefix=f"run_{nm}_")
            rd = run_scan(repo, out, ruleset, budget)
            with open(os.path.join(rd, "report.json"), "r", encoding="utf-8") as f:
                report = json.load(f)
            counts = {}
            for f in report.get("findings", []):
                c = f.get("concept") or ""
                counts[c] = counts.get(c, 0) + 1
            for concept, rng in (expected.get("concept_ranges") or {}).items():
                lo, hi = rng
                v = counts.get(concept, 0)
                self.assertGreaterEqual(v, lo, f"{nm}:{concept} count {v} < {lo}")
                self.assertLessEqual(v, hi, f"{nm}:{concept} count {v} > {hi}")


if __name__ == "__main__":
    unittest.main()
