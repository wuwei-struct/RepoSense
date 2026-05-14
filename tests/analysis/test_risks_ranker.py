import unittest

from reposense.analysis.ai.risks_ranker import rank_risk_items, score_risk_item


class RisksRankerTest(unittest.TestCase):
    def test_score_stable(self):
        item = {"risk_id": "r1", "severity": "high", "status": "confirmed", "pattern_type": "transaction_missing", "evidence_refs": [1, 2], "confidence": 0.8}
        a = score_risk_item(item, gate_obj={"status": "warn"})
        b = score_risk_item(item, gate_obj={"status": "warn"})
        self.assertEqual(a, b)

    def test_rank_order(self):
        rows = rank_risk_items(
            [
                {"risk_id": "low", "severity": "low", "status": "suspected", "pattern_type": "hot_write_path", "evidence_refs": []},
                {"risk_id": "high", "severity": "high", "status": "confirmed", "pattern_type": "transaction_missing", "evidence_refs": [1]},
            ],
            gate_obj={"status": "pass"},
        )
        self.assertEqual(rows[0]["risk_id"], "high")

