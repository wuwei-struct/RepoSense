import os
import json
import unittest
import tempfile
from reposense.scan import run_scan


def fixture_path(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "demo_rules", *p))


class DemoRulesScanSmokeTest(unittest.TestCase):
    def test_demo_rules_scan(self):
        # run scan
        out = tempfile.mkdtemp(prefix="run_demo_")
        rd = run_scan(
            fixture_path(),
            out,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rulesets", "demo_v1")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "presets", "demo.json")),
        )
        report = json.load(open(os.path.join(rd, "report.json"), "r", encoding="utf-8"))
        findings = report.get("findings", [])
        self.assertGreaterEqual(len(findings), 6)
        concepts = {f.get("concept") for f in findings}
        self.assertTrue({"API", "Transaction", "Queue", "Cache", "Idempotency"} & concepts)


if __name__ == "__main__":
    unittest.main()
