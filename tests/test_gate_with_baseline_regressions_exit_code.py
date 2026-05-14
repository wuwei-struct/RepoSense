import os
import json
import tempfile
import subprocess
import sys
import unittest


class GateWithBaselineRegressionsExitCodeTest(unittest.TestCase):
    def test_baseline_gate_exit_codes(self):
        rd = tempfile.mkdtemp(prefix="gate_base_")
        os.makedirs(os.path.join(rd, "exports"), exist_ok=True)
        # base baseline: no error
        base = {"schema_version":1,"findings":[{"fp":"fpX","severity":"note","ruleId":"rX","concept":"X","path":"x.py","startLine":1,"endLine":2}]}
        bpath = os.path.join(rd, "base.json")
        json.dump(base, open(bpath, "w", encoding="utf-8"))
        # new run with an added error via SARIF
        sarif = {"runs":[{"results":[{"ruleId":"rE","level":"error","locations":[{"physicalLocation":{"artifactLocation":{"uri":"e.py"},"region":{"startLine":3,"endLine":4}}}],"fingerprints":{"reposense/v1":"fpE"},"properties":{"concept":"E"}}]}]}
        nrd = os.path.join(rd, "new")
        os.makedirs(os.path.join(nrd, "exports"), exist_ok=True)
        json.dump(sarif, open(os.path.join(nrd, "exports", "report.sarif.json"), "w", encoding="utf-8"))
        # prepare minimal coverage/report for gate to run
        json.dump({"findings":[],"run_summary":{}}, open(os.path.join(nrd, "report.json"), "w", encoding="utf-8"))
        json.dump({"walk":{}}, open(os.path.join(nrd, "coverage.json"), "w", encoding="utf-8"))
        gate_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "gates", "prod_lite.json"))
        p = subprocess.run([sys.executable,"-m","reposense","gate", nrd, "--gate", gate_path, "--baseline", bpath], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
