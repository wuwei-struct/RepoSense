import json
import os
import shutil
import tempfile
import unittest

from reposense.analysis.ai.pattern_export import export_patterns


class PatternEngineSmokeTest(unittest.TestCase):
    def _mk_run_dir(self):
        rd = tempfile.mkdtemp(prefix="pattern-engine-run-")
        os.makedirs(os.path.join(rd, "context_pack", "ARTIFACTS"), exist_ok=True)
        os.makedirs(os.path.join(rd, "context_pack", "MAP"), exist_ok=True)
        os.makedirs(os.path.join(rd, "exports"), exist_ok=True)
        with open(os.path.join(rd, "context_pack", "README.md"), "w", encoding="utf-8") as f:
            f.write("# Pack\n")
        with open(os.path.join(rd, "context_pack", "MAP", "index.json"), "w", encoding="utf-8") as f:
            json.dump({"outputs": {}, "stats": {}}, f)
        report = {
            "findings": [
                {
                    "fid": 1,
                    "concept": "Queue",
                    "rule_id": "queue.dispatch",
                    "confidence": 0.9,
                    "parse_level": "L3",
                    "path": "svc/order.py",
                    "start_line": 10,
                    "end_line": 10,
                    "snippet": "send_message(x)",
                    "primary_eid": 1,
                }
            ],
            "run_summary": {},
        }
        graph = {
            "nodes": [
                {"event_id": 1, "type": "api", "confidence": 0.9, "meta": {"path": "svc/order.py", "start_line": 5, "end_line": 5, "language": "python", "framework": "fastapi"}},
                {"event_id": 2, "type": "db_op", "confidence": 0.9, "meta": {"path": "svc/order.py", "start_line": 8, "end_line": 8, "language": "python", "framework": "django", "db.kind": "db.write"}},
                {"event_id": 3, "type": "queue_dispatch", "confidence": 0.9, "meta": {"path": "svc/order.py", "start_line": 9, "end_line": 9, "language": "python", "framework": "celery", "queue_name": "orders"}},
            ],
            "edges": [],
        }
        with open(os.path.join(rd, "report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f)
        with open(os.path.join(rd, "event_graph.json"), "w", encoding="utf-8") as f:
            json.dump(graph, f)
        with open(os.path.join(rd, "cross_language_summary.json"), "w", encoding="utf-8") as f:
            json.dump({"unmatched_callers": 1, "endpoints_without_callers": 0}, f)
        with open(os.path.join(rd, "cross_language_links.json"), "w", encoding="utf-8") as f:
            json.dump({"unmatched_callers": [{"file": "frontend/client.ts", "line_start": 1, "line_end": 1}], "unmatched_endpoints": []}, f)
        return rd

    def test_export_patterns_smoke(self):
        rd = self._mk_run_dir()
        try:
            res = export_patterns(rd)
            self.assertTrue(os.path.isfile(res["patterns_path"]))
            self.assertTrue(os.path.isfile(res["summary_path"]))
            with open(res["patterns_path"], "r", encoding="utf-8") as f:
                pats = json.load(f).get("patterns") or []
            self.assertTrue(len(pats) >= 1)
            self.assertTrue(all(len((p.get("evidence_refs") or [])) >= 1 for p in pats))
            # context_pack artifacts updated
            self.assertTrue(os.path.isfile(os.path.join(rd, "context_pack", "ARTIFACTS", "patterns.json")))
            self.assertTrue(os.path.isfile(os.path.join(rd, "context_pack", "ARTIFACTS", "pattern_summary.json")))
            # run manifest updated
            self.assertTrue(os.path.isfile(os.path.join(rd, "run_manifest.json")))
            with open(os.path.join(rd, "run_manifest.json"), "r", encoding="utf-8") as f:
                rm = json.load(f)
            paths = set([x.get("path") for x in (rm.get("artifacts") or [])])
            self.assertIn("patterns.json", paths)
            self.assertIn("pattern_summary.json", paths)
        finally:
            shutil.rmtree(rd, ignore_errors=True)
