import os
import json
import tempfile
import unittest
from reposense.ci import run_ci


class ArtifactsStampedWithGeneratedByTest(unittest.TestCase):
    def test_stamps_present(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "entrypoints_min"))
        out = tempfile.mkdtemp(prefix="scan_out_stamp_")
        code = run_ci(repo, out, profile="prod_lite")
        self.assertIn(code, (0,2))
        runs = [os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")]
        run_dir = sorted(runs)[-1]
        for rel in ["report.json","event_graph.json","api_surface.json","entrypoints.json","coverage.json","ci_summary.json","quality_gate.json","run_manifest.json"]:
            p = os.path.join(run_dir, rel)
            self.assertTrue(os.path.isfile(p))
            obj = json.load(open(p, "r", encoding="utf-8"))
            self.assertIsNotNone(obj.get("generated_by"))
            gv = obj.get("generated_by", {}).get("ruleset_fingerprint")
            self.assertTrue(isinstance(gv, str))


if __name__ == "__main__":
    unittest.main()
