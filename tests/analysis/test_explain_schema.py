import unittest

from reposense.analysis.ai.explain_schema import build_explain_request, normalize_explain_result


class ExplainSchemaTest(unittest.TestCase):
    def test_request_stable(self):
        a = build_explain_request("pattern", "p1", with_drilldown=True)
        b = build_explain_request("pattern", "p1", with_drilldown=True)
        self.assertEqual(a["request_id"], b["request_id"])
        self.assertEqual(a["target_type"], "pattern")

    def test_result_normalize(self):
        out = normalize_explain_result(
            {
                "request_id": "ex-1",
                "run_dir": "r",
                "target_type": "finding",
                "target_id": "f1",
                "mode": "facts_only",
                "confirmed": [{"claim": "c", "because": "b", "confidence": 0.8}],
                "inferred": [{"claim": "i", "signals": ["s"], "why_not_confirmed": "w"}],
                "unknown": [{"question": "q", "missing_evidence": ["m"], "suggested_next_step": "n"}],
            }
        )
        self.assertEqual(out["metadata"]["confirmed_count"], 1)
        self.assertEqual(out["metadata"]["inferred_count"], 1)
        self.assertEqual(out["metadata"]["unknown_count"], 1)

