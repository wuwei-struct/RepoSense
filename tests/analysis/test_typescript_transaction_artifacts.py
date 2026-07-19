import json
import os
import shutil
import unittest

from reposense.context_pack import build_context_pack
from reposense.run_manifest import build_run_manifest
from tests.analysis._typescript_transaction_fixture import (
    build_typescript_transaction_run,
    fixture_repo,
)
from tools.validation.typescript_transaction_validation import write_validation


class TypeScriptTransactionArtifactsTest(unittest.TestCase):
    def test_manifest_context_pack_and_validation_artifacts(self):
        run_dir = build_typescript_transaction_run()
        try:
            write_validation(run_dir, fixture_repo())
            build_context_pack(run_dir)
            manifest = build_run_manifest(run_dir)
            paths = {item["path"] for item in manifest["artifacts"]}
            self.assertIn("transaction_correlations.json", paths)
            self.assertIn("typescript_transaction_validation.json", paths)
            self.assertIn(
                "context_pack/ARTIFACTS/typescript_transaction_validation.json",
                paths,
            )
            with open(
                os.path.join(run_dir, "context_pack", "MAP", "index.json"),
                "r",
                encoding="utf-8",
            ) as handle:
                outputs = json.load(handle)["outputs"]
            self.assertIn("typescript_transaction_validation", outputs)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
