import shutil
import unittest
import json

from reposense.context_pack import build_context_pack
from reposense.run_manifest import build_run_manifest
from tests.analysis.test_typescript_import_graph_schema import (
    build_alias_run,
    load_json,
)


class TypeOrmAliasArtifactsTest(unittest.TestCase):
    def test_manifest_and_context_pack_include_resolution_artifacts(self):
        run_dir = build_alias_run()
        try:
            graph_path = run_dir / "event_graph.json"
            graph = load_json(graph_path)
            evidence_id = next(
                value
                for node in graph["nodes"]
                for value in (node.get("evidence") or [])
            )
            graph["nodes"].append(
                {
                    "event_id": "context-pack-transaction",
                    "type": "tx_boundary",
                    "confidence": 0.5,
                    "evidence": [evidence_id],
                    "meta": {"language": "typescript"},
                }
            )
            graph_path.write_text(
                json.dumps(graph), encoding="utf-8"
            )
            build_context_pack(str(run_dir))
            manifest = build_run_manifest(str(run_dir))
            paths = {item["path"] for item in manifest["artifacts"]}
            self.assertIn("typescript_import_graph.json", paths)
            self.assertIn("typeorm_alias_resolutions.json", paths)
            self.assertIn(
                "context_pack/ARTIFACTS/typeorm_alias_resolution_summary.json",
                paths,
            )
            index = load_json(run_dir / "context_pack" / "MAP" / "index.json")
            self.assertIn("typeorm_alias_resolutions", index["outputs"])
        finally:
            shutil.rmtree(run_dir.parent, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
