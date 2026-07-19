import contextlib
import io
import json
import os
import shutil
import unittest

from reposense.ci import run_ci
from reposense.run_manifest import build_run_manifest
from reposense.verifier import run_verify, verify
from tests._tmpdir import make_temp_dir


class StrictVerifyEvidenceLocationsTest(unittest.TestCase):
    def setUp(self):
        self.root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.repo = os.path.join(self.root, "tests", "fixtures", "repos", "java_jpa_mybatis_min")
        self.out = make_temp_dir(prefix="strict_evidence_")
        code = run_ci(self.repo, self.out, profile="demo", with_context_pack=False, json_stdout=False)
        self.assertIn(code, (0, 2))
        self.run_dir = sorted(os.path.join(self.out, name) for name in os.listdir(self.out) if name.startswith("run-"))[-1]

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def test_strict_verify_rejects_zero_line_in_pattern(self):
        self.assertTrue(verify(self.run_dir, strict=True)["ok"])
        path = os.path.join(self.run_dir, "patterns.json")
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        source = next(
            os.path.relpath(os.path.join(base, name), self.repo).replace("\\", "/")
            for base, _dirs, files in os.walk(self.repo)
            for name in files
            if name.endswith(".java")
        )
        payload.setdefault("patterns", []).append(
            {
                "pattern_id": "injected-zero-line",
                "pattern_type": "db_write_outside_tx",
                "severity": "high",
                "status": "confirmed",
                "evidence_refs": [{"source_type": "event", "event_id": "injected", "file": source, "start_line": 0, "end_line": 0}],
            }
        )
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        build_run_manifest(self.run_dir, write=True)

        result = verify(self.run_dir, strict=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any("EVIDENCE_LINE_START_INVALID" in error and "patterns.json" in error for error in result["errors"]))
        with self.assertRaises(SystemExit) as raised:
            with contextlib.redirect_stdout(io.StringIO()):
                run_verify(self.run_dir, as_json=True, strict=True)
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
