import os
import json
import tempfile
import unittest
from reposense.quality_gate import load_gate_config, collect_metrics, evaluate, write_quality_gate


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


class QualityGateSmokePassWarnFailTest(unittest.TestCase):
    def _mk_run(self, skipped_ratio=0.0, artifacts_missing=False, budget_cut=False, mism_spec=0, mism_code=0):
        rd = tempfile.mkdtemp(prefix="gate_run_")
        rep = {"run_summary": {
            "artifacts_missing": (["event_graph.json"] if artifacts_missing else []),
            "truncation": {"budget_cut": budget_cut, "findings_truncated": False, "events_truncated": False},
            "scanned_files": 10,
            "warnings_count": 0,
            "findings_count": 1,
            "events_count": 1,
            "graph_nodes": 1,
            "graph_edges": 0
        }, "findings": []}
        write_json(os.path.join(rd, "report.json"), rep)
        cov = {"walk": {"included_files": 10, "skipped": {"ignored_ext": int(10 * skipped_ratio)}}, "warnings": []}
        write_json(os.path.join(rd, "coverage.json"), cov)
        api = {"mismatches": {"missing_in_spec": list(range(mism_spec)), "missing_in_code": list(range(mism_code))}}
        write_json(os.path.join(rd, "api_surface.json"), api)
        return rd

    def test_pass_warn_fail(self):
        cfg = load_gate_config(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "gates", "prod_lite.json")))
        # PASS
        rd_pass = self._mk_run(skipped_ratio=0.1, artifacts_missing=False, budget_cut=False, mism_spec=0, mism_code=0)
        obj_pass = evaluate(collect_metrics(rd_pass), cfg)
        self.assertEqual(obj_pass.get("status"), "pass")
        # WARN (skipped_ratio high)
        rd_warn = self._mk_run(skipped_ratio=0.8, artifacts_missing=False, budget_cut=False, mism_spec=1, mism_code=0)
        obj_warn = evaluate(collect_metrics(rd_warn), cfg)
        self.assertEqual(obj_warn.get("status"), "warn")
        # FAIL (artifacts missing or budget_cut)
        rd_fail = self._mk_run(skipped_ratio=0.0, artifacts_missing=True, budget_cut=True, mism_spec=0, mism_code=0)
        obj_fail = evaluate(collect_metrics(rd_fail), cfg)
        self.assertEqual(obj_fail.get("status"), "fail")
        write_quality_gate(rd_fail, obj_fail)
        self.assertTrue(os.path.isfile(os.path.join(rd_fail, "quality_gate.json")))


if __name__ == "__main__":
    unittest.main()

