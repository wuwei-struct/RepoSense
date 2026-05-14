import unittest

from reposense.analysis.ai.pattern_schema import (
    make_pattern_id,
    normalize_pattern,
    validate_pattern,
    stable_sort_patterns,
)


class PatternSchemaTest(unittest.TestCase):
    def test_pattern_id_stable(self):
        refs = [
            {"source_type": "finding", "finding_id": 7, "file": "a.py", "start_line": 10, "end_line": 11, "rule_id": "x"},
            {"source_type": "event", "event_id": 3, "file": "a.py", "start_line": 20, "end_line": 20},
        ]
        a = make_pattern_id("transaction_missing", refs)
        b = make_pattern_id("transaction_missing", list(reversed(refs)))
        self.assertEqual(a, b)

    def test_validate_severity_status(self):
        p = normalize_pattern(
            {
                "pattern_type": "db_write_outside_tx",
                "severity": "high",
                "status": "confirmed",
                "confidence": 0.8,
                "evidence_refs": [{"source_type": "event", "event_id": 1, "file": "x.py", "start_line": 1, "end_line": 1}],
            }
        )
        self.assertEqual(validate_pattern(p), [])
        bad = dict(p)
        bad["severity"] = "critical"
        self.assertIn("severity invalid", validate_pattern(bad))

    def test_stable_dedupe_sort_key_material(self):
        p1 = normalize_pattern(
            {
                "pattern_type": "a",
                "severity": "medium",
                "status": "suspected",
                "confidence": 0.3,
                "evidence_refs": [{"source_type": "event", "event_id": 1, "file": "x.py", "start_line": 1, "end_line": 1}],
            }
        )
        p2 = normalize_pattern(
            {
                "pattern_type": "b",
                "severity": "high",
                "status": "confirmed",
                "confidence": 0.9,
                "evidence_refs": [{"source_type": "event", "event_id": 2, "file": "y.py", "start_line": 1, "end_line": 1}],
            }
        )
        arr = stable_sort_patterns([p1, p2])
        self.assertEqual(arr[0]["pattern_type"], "b")

