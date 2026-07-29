import json
import os
import unittest
from pathlib import Path, PurePosixPath

from reposense.analysis.ai.pattern_export import export_patterns
from reposense.analysis.typescript.import_graph import build_typescript_index
from reposense.scan import run_scan
from tests._tmpdir import make_temp_dir


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "repos" / "typeorm_cross_file_alias_min"


def build_alias_run():
    run_dir = make_temp_dir(prefix="typeorm_alias_")
    run_dir = run_scan(
        str(FIXTURE),
        run_dir,
        str(ROOT / "rulesets" / "demo_v1"),
        str(ROOT / "presets" / "demo.json"),
    )
    export_patterns(run_dir)
    return Path(run_dir)


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


class TypeScriptImportGraphSchemaTest(unittest.TestCase):
    def test_symbol_ids_paths_and_evidence_are_stable(self):
        first = build_typescript_index(FIXTURE)
        second = build_typescript_index(FIXTURE)
        self.assertEqual(first["symbol_index"], second["symbol_index"])
        ids = [item["symbol_id"] for item in first["symbols"]]
        self.assertEqual(len(ids), len(set(ids)))
        for item in first["symbols"]:
            self.assertFalse(PurePosixPath(item["file"]).is_absolute())
            for ref in item["evidence_refs"]:
                self.assertGreaterEqual(ref["start_line"], 1)


if __name__ == "__main__":
    unittest.main()
