import os
import tempfile
import unittest
from reposense.ci import run_ci


class BackwardCompatArtifactsStillExistTest(unittest.TestCase):
    def test_legacy_artifacts_compatible(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "demo_showcase"))
        out = tempfile.mkdtemp(prefix="compat_artifacts_")
        code = run_ci(repo, out, profile="demo", with_context_pack=True, json_stdout=False)
        self.assertIn(code, (0, 2))
        rd = sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]
        self.assertTrue(os.path.isfile(os.path.join(rd, "event_graph.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "api_surface.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "entrypoints.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "coverage.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "quality_gate.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "run_manifest.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "language_capabilities.json")))


if __name__ == "__main__":
    unittest.main()
