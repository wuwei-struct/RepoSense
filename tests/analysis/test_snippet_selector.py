import unittest

from reposense.analysis.ai.drilldown_schema import build_request
from reposense.analysis.ai.snippet_selector import select_candidates


class SnippetSelectorTest(unittest.TestCase):
    def _facts(self):
        return {
            "findings": [
                {"fid": "f1", "path": "svc/order.py", "start_line": 10, "end_line": 10, "rule_id": "db.write", "confidence": 0.9}
            ],
            "events": [
                {"event_id": "e1", "confidence": 0.8, "meta": {"path": "svc/order.py", "start_line": 12, "end_line": 12}},
                {"event_id": "e2", "confidence": 0.8, "meta": {"path": "svc/order.py", "start_line": 13, "end_line": 13}},
            ],
            "patterns": [
                {
                    "pattern_id": "p1",
                    "evidence_refs": [
                        {"source_type": "finding", "finding_id": "f1", "file": "svc/order.py", "start_line": 10, "end_line": 10},
                        {"source_type": "event", "event_id": "e1", "file": "svc/order.py", "start_line": 12, "end_line": 12},
                    ],
                    "supporting_findings": ["f1"],
                    "supporting_events": ["e2"],
                }
            ],
        }

    def test_merge_and_budget_clip(self):
        req = build_request(
            "pattern",
            "p1",
            {"context_lines": 2, "max_files": 2, "max_snippets": 2, "max_lines_per_snippet": 8},
        )
        out = select_candidates(self._facts(), req)
        cands = out["candidates"]
        self.assertTrue(len(cands) >= 1)
        self.assertEqual(cands[0]["file"], "svc/order.py")
        self.assertLessEqual(cands[0]["line_end"] - cands[0]["line_start"] + 1, 8)
        self.assertIn("budget_clip", out["selection_trace"]["strategy"])

    def test_finding_target(self):
        req = build_request("finding", "f1", {"max_snippets": 1})
        out = select_candidates(self._facts(), req)
        self.assertEqual(len(out["candidates"]), 1)
        src = out["candidates"][0]["source_refs"][0]
        self.assertEqual(src["finding_id"], "f1")

