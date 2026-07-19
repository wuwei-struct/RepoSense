import importlib.util
import json
import os
import shutil
import unittest

from tests._tmpdir import make_temp_dir


def _load_module():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    path = os.path.join(root, "tools", "validation", "real_repo_smoke.py")
    spec = importlib.util.spec_from_file_location("real_repo_smoke", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RealRepoSmokeSummaryTest(unittest.TestCase):
    def setUp(self):
        self.module = _load_module()
        self.root = make_temp_dir(prefix="real_repo_summary_")
        self.repo = os.path.join(self.root, "repo")
        self.run = os.path.join(self.root, "run")
        os.makedirs(self.repo)
        os.makedirs(self.run)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write_json(self, rel, payload):
        path = os.path.join(self.run, rel)
        os.makedirs(os.path.dirname(path) or self.run, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)

    def test_missing_artifacts_and_inferred_only_are_reported(self):
        self._write_json("coverage.json", {"walk": {"included_files": 1}, "warnings": []})
        self._write_json("authz_matrix_diff.json", {"mode": "inferred_only", "summary": {}, "diffs": []})
        with open(os.path.join(self.run, "authz_matrix_inferred.yaml"), "w", encoding="utf-8") as handle:
            handle.write("inferred: true\nroutes: {}\n")
        validation = self.module.build_case_validation(
            "sample", self.run, self.repo, {}, {"completed": True, "stages": []}
        )
        self.assertFalse(validation["artifact_completeness"]["complete"])
        self.assertIn("report.html", validation["artifact_completeness"]["missing"])
        self.assertEqual(validation["authz_matrix"]["mode"], "inferred_only")
        self.assertTrue(validation["authz_matrix"]["needs_confirmation"])

    def test_evidence_outside_repository_fails_integrity(self):
        outside = os.path.join(self.root, "outside.py")
        with open(outside, "w", encoding="utf-8") as handle:
            handle.write("print('outside')\n")
        self._write_json(
            "report.json",
            {"findings": [{"fid": 1, "path": outside, "start_line": 1, "snippet": "print('outside')"}]},
        )
        integrity = self.module.validate_evidence(self.run, self.repo)
        self.assertFalse(integrity["passed"])
        self.assertIn("EVIDENCE_ABSOLUTE_PATH", {item["type"] for item in integrity["errors"]})
        serialized = json.dumps(integrity)
        self.assertNotIn(os.path.dirname(outside), serialized)

    def test_file_context_uses_nested_evidence_location(self):
        source = os.path.join(self.repo, ".hygen", "template.ts")
        os.makedirs(os.path.dirname(source))
        with open(source, "w", encoding="utf-8") as handle:
            handle.write("template\n")
        self._write_json(
            "file_context_annotations.json",
            {
                "annotations": [
                    {
                        "annotation_id": "file-context-dot-dir",
                        "file": ".hygen/template.ts",
                        "context": "template",
                        "evidence_refs": [
                            {
                                "file": ".hygen/template.ts",
                                "start_line": 1,
                                "end_line": 1,
                                "snippet": "template",
                            }
                        ],
                    }
                ]
            },
        )
        integrity = self.module.validate_evidence(self.run, self.repo)
        self.assertTrue(integrity["passed"], integrity["errors"])

    def test_summary_json_and_markdown_are_written(self):
        case_dir = os.path.join(self.root, "current", "cases", "sample")
        os.makedirs(case_dir, exist_ok=True)
        validation = {
            "case_id": "sample",
            "source": {"name": "Sample", "commit_sha": "abc", "license": "MIT"},
            "execution": {"pipeline_completed": True},
            "strict_verification": {"attempted": True, "passed": True, "exit_code": 0},
            "artifact_completeness": {"complete": True},
            "evidence_integrity": {"passed": True, "errors": []},
            "authz_matrix": {"mode": "inferred_only"},
            "review_statistics": {"review_decision": "WARN"},
            "validation_errors": [],
            "ready_for_manual_calibration": True,
        }
        with open(os.path.join(case_dir, "validation.json"), "w", encoding="utf-8") as handle:
            json.dump(validation, handle)
        summary = self.module.build_overall_summary(os.path.join(self.root, "current"), {"cases": []})
        self.module.write_summary_outputs(os.path.join(self.root, "current"), summary)
        self.assertEqual(summary["status"], "complete")
        self.assertTrue(os.path.isfile(os.path.join(self.root, "current", "summary.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.root, "current", "summary.md")))

    def test_zero_line_fails_integrity_while_strict_result_is_recorded_separately(self):
        source = os.path.join(self.repo, "service.py")
        with open(source, "w", encoding="utf-8") as handle:
            handle.write("save()\n")
        self._write_json(
            "patterns.json",
            {
                "patterns": [
                    {
                        "pattern_id": "bad-line",
                        "pattern_type": "db_write_outside_tx",
                        "evidence_refs": [{"file": "service.py", "start_line": 0, "end_line": 0}],
                    }
                ]
            },
        )
        self._write_json("coverage.json", {"walk": {"included_files": 1}, "warnings": []})
        self._write_json("authz_matrix_diff.json", {"mode": "inferred_only", "summary": {}, "diffs": []})
        with open(os.path.join(self.run, "authz_matrix_inferred.yaml"), "w", encoding="utf-8") as handle:
            handle.write("inferred: true\nroutes: {}\n")
        validation = self.module.build_case_validation(
            "sample",
            self.run,
            self.repo,
            {},
            {"completed": True, "stages": [{"stage": "verify_strict", "ok": True, "exit_code": 0}]},
        )
        self.assertTrue(validation["strict_verification"]["passed"])
        self.assertFalse(validation["evidence_integrity"]["passed"])
        self.assertFalse(validation["ready_for_manual_calibration"])
        self.assertIn("EVIDENCE_LINE_START_INVALID", {row["error_code"] for row in validation["evidence_integrity"]["errors"]})


if __name__ == "__main__":
    unittest.main()
