import os
import tempfile
import unittest
from reposense.ci import run_ci


class DemoShowcaseScanSmokeTest(unittest.TestCase):
    def test_scan_produces_artifacts(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "demo_showcase"))
        out = tempfile.mkdtemp(prefix="demo_scan_")
        code = run_ci(repo, out, profile="demo", with_context_pack=True, json_stdout=False)
        self.assertIn(code, (0,2))
        rd = sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]
        self.assertTrue(os.path.isfile(os.path.join(rd, "report.html")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "exports", "report.sarif.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "exports", "context_pack.zip")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "quality_gate.json")))


if __name__ == "__main__":
    unittest.main()
