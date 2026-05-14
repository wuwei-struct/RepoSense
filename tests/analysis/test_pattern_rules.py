import unittest

from reposense.analysis.ai.pattern_rules import run_all_rules


def _ctx_base():
    return {
        "findings": [],
        "events": [],
        "cross_language_summary": {},
        "cross_language_links": {},
    }


class PatternRulesTest(unittest.TestCase):
    def test_tx_missing_and_db_outside_tx(self):
        ctx = _ctx_base()
        ctx["events"] = [
            {"event_id": 1, "type": "api", "confidence": 0.9, "meta": {"path": "app/api.py", "start_line": 10, "end_line": 10, "language": "python", "framework": "fastapi"}},
            {"event_id": 2, "type": "db_op", "confidence": 0.9, "meta": {"path": "app/api.py", "start_line": 12, "end_line": 12, "language": "python", "framework": "django", "db.kind": "db.write"}},
        ]
        pats = run_all_rules(ctx)
        types = set([p["pattern_type"] for p in pats])
        self.assertIn("transaction_missing", types)
        self.assertIn("db_write_outside_tx", types)

    def test_queue_without_consumer_suspected_when_name_missing(self):
        ctx = _ctx_base()
        ctx["events"] = [
            {"event_id": 11, "type": "queue_dispatch", "confidence": 0.7, "meta": {"path": "worker.py", "start_line": 3, "end_line": 3, "language": "python", "framework": "celery"}}
        ]
        pats = run_all_rules(ctx)
        q = [p for p in pats if p["pattern_type"] == "queue_without_consumer"]
        self.assertTrue(len(q) >= 1)
        self.assertEqual(q[0]["status"], "suspected")

    def test_cross_language_unmatched(self):
        ctx = _ctx_base()
        ctx["cross_language_summary"] = {"unmatched_callers": 2, "endpoints_without_callers": 1}
        ctx["cross_language_links"] = {
            "unmatched_callers": [{"file": "frontend/client.ts", "line_start": 12, "line_end": 12}],
            "unmatched_endpoints": [{"file": "backend/api.py", "line_start": 44, "line_end": 44}],
        }
        pats = run_all_rules(ctx)
        types = [p["pattern_type"] for p in pats]
        self.assertIn("cross_language_api_unmatched", types)

    def test_api_write_without_guard(self):
        ctx = _ctx_base()
        ctx["events"] = [
            {"event_id": 21, "type": "api", "confidence": 0.8, "meta": {"path": "service.py", "start_line": 8, "end_line": 8, "language": "python", "framework": "fastapi"}},
            {"event_id": 22, "type": "db_op", "confidence": 0.8, "meta": {"path": "service.py", "start_line": 12, "end_line": 12, "language": "python", "framework": "django", "db.kind": "db.write"}},
        ]
        pats = run_all_rules(ctx)
        target = [p for p in pats if p["pattern_type"] == "api_write_without_idempotency_guard"]
        self.assertTrue(len(target) >= 1)
        self.assertEqual(target[0]["status"], "suspected")

