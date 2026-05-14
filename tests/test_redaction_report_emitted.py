import os
import json
import tempfile
import unittest
from reposense.ci import run_ci


class RedactionReportEmittedTest(unittest.TestCase):
    def test_redaction_report(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "demo_showcase"))
        out = tempfile.mkdtemp(prefix="redact_rep_")
        os.environ["REPOSENSE_REDACT"] = "1"
        code = run_ci(repo, out, profile="demo", with_context_pack=True, json_stdout=False)
        self.assertIn(code, (0,2))
        rd = sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]
        rp = os.path.join(rd, "redaction_report.json")
        self.assertTrue(os.path.isfile(rp))
        obj = json.load(open(rp, "r", encoding="utf-8"))
        self.assertTrue("counts" in obj)
        self.assertTrue("files" in obj)


if __name__ == "__main__":
    unittest.main()
