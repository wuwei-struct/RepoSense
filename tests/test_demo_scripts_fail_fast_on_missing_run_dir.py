import os
import unittest


class DemoScriptsFailFastStructureTest(unittest.TestCase):
    def test_bash_script_has_failfast_and_checks(self):
        p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "demo_run.sh"))
        txt = open(p, "r", encoding="utf-8").read()
        self.assertIn("set -euo pipefail", txt)
        self.assertIn("baseline run_dir invalid", txt)
        self.assertIn("regress run_dir invalid", txt)
        self.assertIn("missing report.html", txt)
        self.assertIn("missing learn/index.html", txt)
        self.assertIn("missing exports/report.sarif.json", txt)
        self.assertIn("missing exports/context_pack.zip", txt)
        self.assertIn("missing quality_gate.json", txt)
        self.assertIn("missing baseline_diff.md", txt)
    def test_ps1_script_has_failfast_and_checks(self):
        p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "demo_run.ps1"))
        txt = open(p, "r", encoding="utf-8").read()
        self.assertIn("$ErrorActionPreference = \"Stop\"", txt)
        self.assertIn("baseline run_dir invalid", txt)
        self.assertIn("regress run_dir invalid", txt)
        self.assertIn("missing report.html", txt)
        self.assertIn("missing learn/index.html", txt)
        self.assertIn("missing exports/report.sarif.json", txt)
        self.assertIn("missing exports/context_pack.zip", txt)
        self.assertIn("missing quality_gate.json", txt)
        self.assertIn("missing baseline_diff.md", txt)


if __name__ == "__main__":
    unittest.main()
