import json
import os
import unittest

from reposense.context_pack import build_context_pack
from reposense.run_manifest import build_run_manifest
from tests.analysis.test_queue_reliability_schema import (
    build_queue_reliability_run,
)


class QueueReliabilityArtifactsTest(unittest.TestCase):
    def test_manifest_context_pack_and_evidence_lines(self):
        run_dir = build_queue_reliability_run()
        build_context_pack(run_dir)
        manifest = build_run_manifest(run_dir, write=False)
        paths = {item["path"] for item in manifest["artifacts"]}
        self.assertIn("queue_reliability_correlations.json", paths)
        self.assertIn(
            "context_pack/ARTIFACTS/queue_reliability_summary.json", paths
        )
        with open(
            os.path.join(run_dir, "context_pack", "MAP", "index.json"),
            encoding="utf-8",
        ) as handle:
            index = json.load(handle)
        self.assertIn("queue_reliability_correlations", index["outputs"])
        with open(
            os.path.join(run_dir, "queue_reliability_correlations.json"),
            encoding="utf-8",
        ) as handle:
            artifact = json.load(handle)
        refs = [
            ref
            for item in artifact["correlations"]
            for ref in item["evidence_refs"]
        ]
        self.assertTrue(refs)
        self.assertTrue(all(ref["start_line"] >= 1 for ref in refs))


if __name__ == "__main__":
    unittest.main()
