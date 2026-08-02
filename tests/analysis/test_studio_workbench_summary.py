import json
import os
import tempfile
import unittest

from reposense.studio.run_summary import build_run_summary


def _write(root, name, value):
    path = os.path.join(root, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle)


class StudioWorkbenchSummaryTest(unittest.TestCase):
    def test_overview_counts_and_actions_use_existing_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            _write(td, "api_surface.json", {"endpoints": [{}, {}]})
            _write(td, "repository_review_report.json", {
                "review_summary": {"decision": "REVIEW", "human_review_required_count": 2},
                "queue_cache_review": {"backend_event_counts": {
                    "db.read": 1, "db.write": 2, "queue.dispatch": 1,
                    "queue.consume": 0, "cache.read": 1,
                }},
            })
            _write(td, "transaction_correlation_summary.json", {
                "total_correlations": 3,
                "counts_by_coverage_status": {"covered_explicit": 1, "unknown": 2},
            })
            _write(td, "permission_risks.json", {"risks": []})
            _write(td, "code_health_summary.json", {
                "total_findings": 0,
                "counts_by_severity": {},
                "health_score": {"enabled": True, "score": 100},
            })
            for name in (
                "human_review_required.md",
                "permission_risk_report.md",
                "quality_gate.json",
                "context_pack/REVIEW/README.md",
            ):
                path = os.path.join(td, name)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                if not os.path.exists(path):
                    with open(path, "w", encoding="utf-8") as handle:
                        handle.write("artifact")
            summary = build_run_summary(td)
        self.assertEqual(summary["review_decision"], "REVIEW")
        self.assertEqual(summary["repository_facts"]["api_endpoints"]["value"], 2)
        self.assertEqual(summary["repository_facts"]["code_health_findings"], {
            "value": 0,
            "availability": "available",
        })
        self.assertEqual(summary["domain_summaries"]["transactions"]["unknown"], 2)
        self.assertIn("review_human_items", {
            item["action_id"] for item in summary["recommended_actions"]
        })

    def test_missing_and_malformed_are_distinct(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "code_health_summary.json"), "w", encoding="utf-8") as handle:
                handle.write("{bad json")
            summary = build_run_summary(td)
        self.assertEqual(summary["artifact_states"]["code_health_summary.json"], "malformed")
        self.assertEqual(summary["artifact_states"]["permission_risks.json"], "not_generated")
        self.assertEqual(summary["domain_summaries"]["code_health"]["availability"], "malformed")


if __name__ == "__main__":
    unittest.main()
