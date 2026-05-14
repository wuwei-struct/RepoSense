import json
import os
import tempfile


def build_drilldown_run_dir():
    repo = tempfile.mkdtemp(prefix="repo_drilldown_")
    run_dir = tempfile.mkdtemp(prefix="run_drilldown_")
    os.makedirs(os.path.join(repo, "svc"), exist_ok=True)
    src = [
        "from fastapi import FastAPI",
        "app = FastAPI()",
        "@app.post('/orders')",
        "def create_order(req):",
        "    user_id = req.get('uid')",
        "    payload = {'uid': user_id}",
        "    db_write(payload)",
        "    queue_send('orders', payload)",
        "    return {'ok': True}",
    ]
    with open(os.path.join(repo, "svc", "order.py"), "w", encoding="utf-8") as f:
        f.write("\n".join(src) + "\n")
    with open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"repo_root": repo, "timestamp": 1773381901640}, f)
    report = {
        "findings": [
            {
                "fid": "f-1",
                "concept": "transaction",
                "rule_id": "db.write",
                "confidence": 0.9,
                "path": "svc/order.py",
                "start_line": 7,
                "end_line": 7,
                "snippet": "db_write(payload)",
            }
        ],
        "run_summary": {"scanned_files": 1, "findings_count": 1},
    }
    graph = {
        "nodes": [
            {"event_id": "e-1", "type": "api", "confidence": 0.9, "meta": {"path": "svc/order.py", "start_line": 3, "end_line": 4}},
            {"event_id": "e-2", "type": "db_op", "confidence": 0.9, "meta": {"path": "svc/order.py", "start_line": 7, "end_line": 7, "db.kind": "db.write"}},
            {"event_id": "e-3", "type": "queue_dispatch", "confidence": 0.88, "meta": {"path": "svc/order.py", "start_line": 8, "end_line": 8, "queue_name": "orders"}},
        ],
        "edges": [],
    }
    pattern = {
        "pattern_id": "pat-1",
        "pattern_type": "transaction_missing",
        "title": "Write path lacks transaction boundary",
        "severity": "high",
        "confidence": 0.84,
        "summary": "api+db write without tx",
        "supporting_findings": ["f-1"],
        "supporting_events": ["e-1", "e-2"],
        "evidence_refs": [
            {"source_type": "finding", "finding_id": "f-1", "file": "svc/order.py", "start_line": 7, "end_line": 7, "rule_id": "db.write"},
            {"source_type": "event", "event_id": "e-1", "file": "svc/order.py", "start_line": 3, "end_line": 4},
        ],
        "files": ["svc/order.py"],
        "languages": ["python"],
        "frameworks": ["fastapi"],
        "status": "confirmed",
        "explain_stub": "add tx",
        "metadata": {},
    }
    with open(os.path.join(run_dir, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f)
    with open(os.path.join(run_dir, "event_graph.json"), "w", encoding="utf-8") as f:
        json.dump(graph, f)
    with open(os.path.join(run_dir, "patterns.json"), "w", encoding="utf-8") as f:
        json.dump({"patterns": [pattern]}, f)
    with open(os.path.join(run_dir, "pattern_summary.json"), "w", encoding="utf-8") as f:
        json.dump({"total_patterns": 1, "counts_by_type": {"transaction_missing": 1}}, f)
    # optional artifacts referenced by run_manifest paths
    with open(os.path.join(run_dir, "coverage.json"), "w", encoding="utf-8") as f:
        json.dump({"walk": {"included_files": 1}}, f)
    with open(os.path.join(run_dir, "quality_gate.json"), "w", encoding="utf-8") as f:
        json.dump({"status": "pass"}, f)
    return run_dir
