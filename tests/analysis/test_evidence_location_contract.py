import os
import shutil
import unittest

from reposense.evidence.validation import (
    EVIDENCE_ABSOLUTE_PATH,
    EVIDENCE_LINE_OUT_OF_RANGE,
    EVIDENCE_LINE_RANGE_INVALID,
    EVIDENCE_LINE_START_INVALID,
    validate_evidence_location,
)
from tests._tmpdir import make_temp_dir


class EvidenceLocationContractTest(unittest.TestCase):
    def setUp(self):
        self.root = make_temp_dir(prefix="evidence_location_")
        self.source = os.path.join(self.root, "src", "service.py")
        os.makedirs(os.path.dirname(self.source))
        with open(self.source, "w", encoding="utf-8") as handle:
            handle.write("one\ntwo\nthree\n")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _codes(self, ref):
        return {
            issue["error_code"]
            for issue in validate_evidence_location(ref, self.root, artifact="test.json", item_id="item")
        }

    def test_valid_relative_location(self):
        self.assertEqual(self._codes({"file": "src/service.py", "start_line": 1, "end_line": 2}), set())

    def test_dot_directory_name_is_preserved(self):
        generated = os.path.join(self.root, ".hygen", "template.ts")
        os.makedirs(os.path.dirname(generated))
        with open(generated, "w", encoding="utf-8") as handle:
            handle.write("template\n")
        self.assertEqual(
            self._codes({"file": ".hygen/template.ts", "start_line": 1, "end_line": 1}),
            set(),
        )

    def test_zero_and_negative_start_are_invalid(self):
        self.assertIn(EVIDENCE_LINE_START_INVALID, self._codes({"file": "src/service.py", "start_line": 0, "end_line": 0}))
        self.assertIn(EVIDENCE_LINE_START_INVALID, self._codes({"file": "src/service.py", "start_line": -1, "end_line": 1}))

    def test_invalid_range_and_out_of_range(self):
        self.assertIn(EVIDENCE_LINE_RANGE_INVALID, self._codes({"file": "src/service.py", "start_line": 2, "end_line": 1}))
        self.assertIn(EVIDENCE_LINE_OUT_OF_RANGE, self._codes({"file": "src/service.py", "start_line": 4, "end_line": 4}))

    def test_absolute_path_is_invalid_for_serialized_ref(self):
        self.assertIn(EVIDENCE_ABSOLUTE_PATH, self._codes({"file": self.source, "start_line": 1, "end_line": 1}))


if __name__ == "__main__":
    unittest.main()
