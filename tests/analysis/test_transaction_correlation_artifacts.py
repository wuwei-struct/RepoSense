import json
import os
import shutil
import unittest

from reposense.context_pack import build_context_pack
from reposense.run_manifest import build_run_manifest
from tests.analysis._transaction_correlation_fixture import build_transaction_run


class TransactionCorrelationArtifactsTest(unittest.TestCase):
    def test_manifest_and_context_pack_include_artifacts(self):
        run_dir = build_transaction_run()
        try:
            manifest = build_run_manifest(run_dir)
            paths = {row["path"] for row in manifest["artifacts"]}
            self.assertIn("transaction_correlations.json", paths)
            self.assertIn("transaction_correlation_summary.json", paths)
            pack = build_context_pack(run_dir)
            for name in ["transaction_correlations.json", "transaction_correlation_summary.json"]:
                self.assertTrue(os.path.isfile(os.path.join(pack, "ARTIFACTS", name)))
            with open(os.path.join(pack, "MAP", "index.json"), "r", encoding="utf-8") as handle:
                outputs = json.load(handle)["outputs"]
            self.assertIn("transaction_correlations", outputs)
            self.assertIn("transaction_correlation_summary", outputs)
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            self.assertTrue(os.path.isfile(os.path.join(root, "docs", "validation", "SPRING_TRANSACTION_CORRELATION.md")))
            with open(os.path.join(root, "docs", "INDEX.md"), "r", encoding="utf-8") as handle:
                self.assertIn("SPRING_TRANSACTION_CORRELATION.md", handle.read())
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
