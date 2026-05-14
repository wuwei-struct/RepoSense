import os
import json
import tempfile
import subprocess
import sys
import unittest
from reposense.versioning import ruleset_fingerprint


class GateBaselineIncompatibleDegradesToAbsoluteTest(unittest.TestCase):
    def test_baseline_incompatible_warn_and_absolute(self):
        rd = tempfile.mkdtemp(prefix="gate_incompat_")
        os.makedirs(os.path.join(rd, "exports"), exist_ok=True)
        json.dump({"findings":[],"run_summary":{"ruleset":"rulesets/specs_v2"}}, open(os.path.join(rd, "report.json"), "w", encoding="utf-8"))
        json.dump({"walk":{}}, open(os.path.join(rd, "coverage.json"), "w", encoding="utf-8"))
        base = {"schema_version":1,"ruleset":"other_rules","ruleset_fingerprint":"aaaaaaaaaaaaaaaa","findings":[]}
        bpath = os.path.join(rd, "baseline.json")
        json.dump(base, open(bpath, "w", encoding="utf-8"))
        gate_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "gates", "prod_lite.json"))
        p = subprocess.run([sys.executable,"-m","reposense","gate", rd, "--gate", gate_path, "--baseline", bpath], capture_output=True, text=True)
        self.assertIn(p.returncode, (0,2))
        q = json.load(open(os.path.join(rd, "quality_gate.json"), "r", encoding="utf-8"))
        self.assertTrue(q.get("baseline_used"))
        self.assertFalse(q.get("baseline_compatible"))
        v = q.get("violations", [])
        self.assertTrue(any(x.get("metric") == "baseline_incompatible" for x in v))


if __name__ == "__main__":
    unittest.main()
