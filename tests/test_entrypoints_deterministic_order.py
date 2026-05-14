import os
import json
import tempfile
import unittest
from reposense.scan import run_scan


class EntryPointsDeterministicOrderTest(unittest.TestCase):
    def test_entrypoints_order_stable(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "entrypoints_min"))
        out1 = tempfile.mkdtemp(prefix="entry_run1_")
        out2 = tempfile.mkdtemp(prefix="entry_run2_")
        r1 = run_scan(repo, out1, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2")), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json")))
        r2 = run_scan(repo, out2, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2")), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json")))
        d1 = json.load(open(os.path.join(r1, "entrypoints.json"), "r", encoding="utf-8"))
        d2 = json.load(open(os.path.join(r2, "entrypoints.json"), "r", encoding="utf-8"))
        self.assertEqual(d1.get("entrypoints", []), d2.get("entrypoints", []))


if __name__ == "__main__":
    unittest.main()

