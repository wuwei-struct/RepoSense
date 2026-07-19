import json
import os
import shutil
import unittest

from reposense.context_pack import build_context_pack
from reposense.evidence.validation import (
    validate_run_evidence_locations,
)
from reposense.run_manifest import build_run_manifest
from tests.analysis._guard_correlation_fixture import (
    build_guard_run,
    fixture_repo,
)


class GuardCorrelationArtifactsTest(unittest.TestCase):
    def test_manifest_context_pack_and_evidence_contract(self):
        run_dir, result = build_guard_run()
        try:
            for key in (
                "correlations_path",
                "summary_path",
                "openapi_security_path",
            ):
                self.assertTrue(
                    os.path.isfile(result["guard_correlation"][key])
                )
            manifest = build_run_manifest(run_dir)
            artifacts = {
                row["path"]: row["kind"] for row in manifest["artifacts"]
            }
            for name in (
                "route_guard_correlations.json",
                "route_guard_summary.json",
                "openapi_security_surface.json",
            ):
                self.assertEqual(
                    artifacts[name], "route_guard_correlation"
                )
            pack = build_context_pack(run_dir)
            for name in (
                "route_guard_correlations.json",
                "route_guard_summary.json",
                "openapi_security_surface.json",
            ):
                self.assertTrue(
                    os.path.isfile(
                        os.path.join(pack, "ARTIFACTS", name)
                    )
                )
            with open(
                os.path.join(pack, "MAP", "index.json"),
                "r",
                encoding="utf-8",
            ) as handle:
                outputs = json.load(handle)["outputs"]
            self.assertIn("route_guard_correlations", outputs)
            self.assertIn("route_guard_summary", outputs)
            self.assertIn("openapi_security_surface", outputs)
            self.assertEqual(
                validate_run_evidence_locations(
                    run_dir, fixture_repo()
                ),
                [],
            )
            root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..")
            )
            docs_path = os.path.join(
                root,
                "docs",
                "validation",
                "OPENAPI_GLOBAL_GUARD_CORRELATION.md",
            )
            self.assertTrue(os.path.isfile(docs_path))
            with open(
                os.path.join(root, "docs", "INDEX.md"),
                "r",
                encoding="utf-8",
            ) as handle:
                self.assertIn(
                    "OPENAPI_GLOBAL_GUARD_CORRELATION.md",
                    handle.read(),
                )
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
