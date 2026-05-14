import json
import os
import tempfile


def build_ai_summary_run_dir():
    rd = tempfile.mkdtemp(prefix="ai-summary-run-")
    os.makedirs(os.path.join(rd, "context_pack", "ARTIFACTS"), exist_ok=True)
    os.makedirs(os.path.join(rd, "context_pack", "MAP"), exist_ok=True)
    with open(os.path.join(rd, "context_pack", "README.md"), "w", encoding="utf-8") as f:
        f.write("# Context Pack\n")
    with open(os.path.join(rd, "context_pack", "MAP", "index.json"), "w", encoding="utf-8") as f:
        json.dump({"outputs": {}, "stats": {}}, f)
    report = {
        "run_summary": {
            "detected_languages": ["python", "typescript"],
            "detected_frameworks": ["fastapi", "express"],
            "scanned_files": 5,
            "findings_count": 3,
            "events_count": 6,
            "graph_edges": 4,
        },
        "findings": [
            {
                "fid": 1,
                "concept": "Transaction",
                "rule_id": "tx.required",
                "confidence": 0.9,
                "path": "svc/order.py",
                "start_line": 10,
                "end_line": 10,
                "snippet": "db.write()",
            }
        ],
    }
    graph = {
        "nodes": [
            {"event_id": "e1", "type": "api", "meta": {"path": "svc/order.py", "start_line": 5, "end_line": 5, "language": "python", "framework": "fastapi"}},
            {"event_id": "e2", "type": "db_op", "meta": {"path": "svc/order.py", "start_line": 6, "end_line": 6, "language": "python", "framework": "django", "db.kind": "db.write"}},
            {"event_id": "e3", "type": "queue_dispatch", "meta": {"path": "svc/order.py", "start_line": 7, "end_line": 7, "language": "python", "framework": "celery", "queue_name": "orders"}},
            {"event_id": "e4", "type": "cache_op", "meta": {"path": "svc/order.py", "start_line": 8, "end_line": 8, "language": "python", "framework": "redis", "cache.kind": "cache.write"}},
        ],
        "edges": [{"from": "e1", "to": "e2", "type": "calls"}],
    }
    api_surface = {"stats": {"unique_endpoints": 2, "by_source_kind": {"openapi": 1}}, "endpoints": [{"method": "POST", "path": "/orders"}]}
    coverage = {"walk": {"included_files": 5}, "warnings": []}
    gate = {"status": "warn", "violations": [{"metric": "api.missing_in_spec_count"}]}
    patterns = {
        "patterns": [
            {
                "pattern_id": "p1",
                "pattern_type": "db_write_outside_tx",
                "severity": "high",
                "confidence": 0.9,
                "summary": "db write no tx",
                "status": "confirmed",
                "evidence_refs": [{"source_type": "event", "event_id": "e2", "file": "svc/order.py", "start_line": 6, "end_line": 6, "rule_id": ""}],
                "files": ["svc/order.py"],
                "languages": ["python"],
                "frameworks": ["django"],
            },
            {
                "pattern_id": "p2",
                "pattern_type": "cross_language_api_unmatched",
                "severity": "medium",
                "confidence": 0.8,
                "summary": "unmatched",
                "status": "suspected",
                "evidence_refs": [{"source_type": "cross_language", "file": "frontend/client.ts", "start_line": 12, "end_line": 12, "rule_id": "cross"}],
                "files": ["frontend/client.ts"],
                "languages": ["typescript"],
                "frameworks": [],
            },
        ]
    }
    pattern_summary = {
        "total_patterns": 2,
        "counts_by_type": {"db_write_outside_tx": 1, "cross_language_api_unmatched": 1},
        "counts_by_severity": {"high": 1, "medium": 1},
        "counts_by_status": {"confirmed": 1, "suspected": 1},
    }
    cross_summary = {"unmatched_callers": 1, "endpoints_without_callers": 1, "matched_links": 0}
    cross_links = {
        "unmatched_callers": [{"file": "frontend/client.ts", "line_start": 12, "line_end": 12}],
        "unmatched_endpoints": [{"file": "backend/api.py", "line_start": 33, "line_end": 33}],
    }
    manifest = {"timestamp": 1234567890}
    for nm, obj in [
        ("report.json", report),
        ("event_graph.json", graph),
        ("api_surface.json", api_surface),
        ("coverage.json", coverage),
        ("quality_gate.json", gate),
        ("patterns.json", patterns),
        ("pattern_summary.json", pattern_summary),
        ("cross_language_summary.json", cross_summary),
        ("cross_language_links.json", cross_links),
        ("manifest.json", manifest),
    ]:
        with open(os.path.join(rd, nm), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
    return rd

