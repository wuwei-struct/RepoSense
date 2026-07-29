import shutil
import unittest
import json

from reposense.evidence.validation import validate_run_evidence_locations
from tools.validation.typeorm_alias_validation import (
    build_triage_items,
    write_validation,
)
from tests.analysis.test_typescript_import_graph_schema import (
    FIXTURE,
    build_alias_run,
)


class TypeOrmAliasRealRepoValidationTest(unittest.TestCase):
    def test_validation_uses_unreviewed_triage_and_valid_evidence(self):
        run_dir = build_alias_run()
        try:
            payload = write_validation(run_dir, FIXTURE)
            self.assertEqual(payload["summary"]["evidence_errors"], 0)
            self.assertGreater(
                payload["summary"]["resolved_wrapper_calls"], 0
            )
            self.assertTrue(
                all(
                    item["triage_status"] == "unreviewed"
                    for item in build_triage_items(payload["resolutions"])
                )
            )
            self.assertTrue((run_dir / "typeorm_alias_validation.md").is_file())
        finally:
            shutil.rmtree(run_dir.parent, ignore_errors=True)

    def test_strict_evidence_validation_rejects_zero_line_alias_ref(self):
        run_dir = build_alias_run()
        try:
            path = run_dir / "typeorm_alias_resolutions.json"
            artifact = json.loads(path.read_text(encoding="utf-8"))
            ref = artifact["resolutions"][0]["callsite_evidence_refs"][0]
            ref["start_line"] = 0
            ref["end_line"] = 0
            path.write_text(json.dumps(artifact), encoding="utf-8")
            issues = validate_run_evidence_locations(run_dir, FIXTURE)
            self.assertTrue(
                any(
                    item["artifact"] == "typeorm_alias_resolutions.json"
                    and item["error_code"]
                    == "EVIDENCE_LINE_START_INVALID"
                    for item in issues
                )
            )
        finally:
            shutil.rmtree(run_dir.parent, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
