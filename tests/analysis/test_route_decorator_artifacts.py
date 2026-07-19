import json
import os
import shutil
import unittest

from reposense.context_pack import build_context_pack
from reposense.evidence.validation import validate_run_evidence_locations
from reposense.run_manifest import build_run_manifest
from tests.analysis._route_decorator_fixture import (
    build_decorator_run,
    fixture_repo,
)


class RouteDecoratorArtifactsTest(unittest.TestCase):
    def test_manifest_context_pack_and_evidence(self):
        run_dir, _result = build_decorator_run()
        try:
            manifest = build_run_manifest(run_dir)
            artifacts = {
                row["path"]: row["kind"] for row in manifest["artifacts"]
            }
            for name in (
                "route_decorator_classifications.json",
                "route_decorator_summary.json",
            ):
                self.assertEqual(
                    artifacts[name],
                    "route_decorator_classification",
                )
            pack = build_context_pack(run_dir)
            for name in (
                "route_decorator_classifications.json",
                "route_decorator_summary.json",
            ):
                self.assertTrue(
                    os.path.isfile(os.path.join(pack, "ARTIFACTS", name))
                )
            with open(
                os.path.join(pack, "MAP", "index.json"),
                "r",
                encoding="utf-8",
            ) as handle:
                outputs = json.load(handle)["outputs"]
            self.assertIn("route_decorator_classifications", outputs)
            self.assertIn("route_decorator_summary", outputs)
            self.assertEqual(
                validate_run_evidence_locations(run_dir, fixture_repo()),
                [],
            )
            root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..")
            )
            doc_path = os.path.join(
                root,
                "docs",
                "validation",
                "ROUTE_DECORATOR_CLASSIFICATION.md",
            )
            self.assertTrue(os.path.isfile(doc_path))
            with open(
                os.path.join(root, "docs", "INDEX.md"),
                "r",
                encoding="utf-8",
            ) as handle:
                self.assertIn(
                    "ROUTE_DECORATOR_CLASSIFICATION.md",
                    handle.read(),
                )
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
