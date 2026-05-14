import os
import json
import tempfile
import unittest
from reposense.ci import run_ci


class RedactionIsDeterministicTest(unittest.TestCase):
    def test_deterministic(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "demo_showcase"))
        out1 = tempfile.mkdtemp(prefix="redet_1_")
        out2 = tempfile.mkdtemp(prefix="redet_2_")
        os.environ["REPOSENSE_REDACT"] = "1"
        code1 = run_ci(repo, out1, profile="demo", with_context_pack=True, json_stdout=False)
        code2 = run_ci(repo, out2, profile="demo", with_context_pack=True, json_stdout=False)
        self.assertIn(code1, (0,2))
        self.assertIn(code2, (0,2))
        rd1 = sorted([os.path.join(out1, d) for d in os.listdir(out1) if d.startswith("run-")])[-1]
        rd2 = sorted([os.path.join(out2, d) for d in os.listdir(out2) if d.startswith("run-")])[-1]
        r1 = json.load(open(os.path.join(rd1, "redaction_report.json"), "r", encoding="utf-8"))
        r2 = json.load(open(os.path.join(rd2, "redaction_report.json"), "r", encoding="utf-8"))
        self.assertEqual(r1.get("counts"), r2.get("counts"))
