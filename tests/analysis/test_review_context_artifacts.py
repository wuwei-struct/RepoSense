import json
import os
import unittest

from reposense.analysis.authz.authz_export import export_permission_auditor
from reposense.analysis.health.health_export import export_code_health
from reposense.context_pack import build_context_pack
from reposense.run_manifest import build_run_manifest
from tests.analysis._review_context_fixture import build_context_run, fixture_repo


class ReviewContextArtifactsTest(unittest.TestCase):
    def test_manifest_and_context_pack_include_context_artifacts(self):
        run_dir = build_context_run()
        export_code_health(run_dir, repo_path=fixture_repo())
        export_permission_auditor(run_dir, repo_path=fixture_repo())
        names = [
            "route_intent_annotations.json",
            "file_context_annotations.json",
            "review_context_summary.json",
        ]
        for name in names:
            self.assertTrue(os.path.isfile(os.path.join(run_dir, name)), name)

        manifest = build_run_manifest(run_dir, write=True)
        manifest_rows = {
            row["path"]: row["kind"] for row in manifest["artifacts"]
        }
        for name in names:
            self.assertEqual(manifest_rows[name], "review_context")

        pack = build_context_pack(run_dir)
        for name in names:
            self.assertTrue(os.path.isfile(os.path.join(pack, "ARTIFACTS", name)))
        with open(os.path.join(pack, "MAP", "index.json"), "r", encoding="utf-8") as handle:
            outputs = json.load(handle)["outputs"]
        self.assertIn("route_intent_annotations", outputs)
        self.assertIn("file_context_annotations", outputs)
        self.assertIn("review_context_summary", outputs)


if __name__ == "__main__":
    unittest.main()
