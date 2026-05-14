import json
import os
import tempfile


def build_studio_ai_run_dir(with_ai=True):
    rd = tempfile.mkdtemp(prefix="studio_ai_run_")
    os.makedirs(os.path.join(rd, "meta"), exist_ok=True)
    with open(os.path.join(rd, "meta", "config.json"), "w", encoding="utf-8") as f:
        json.dump({"profile": "demo"}, f)
    with open(os.path.join(rd, "report.json"), "w", encoding="utf-8") as f:
        json.dump({"findings": [{"fid": "f1", "concept": "transaction", "confidence": 0.9, "parse_level": "L2", "path": "svc/a.py", "start_line": 3, "end_line": 3, "snippet": "db_write()"}], "run_summary": {"findings_count": 1, "events_count": 1}}, f)
    with open(os.path.join(rd, "event_graph.json"), "w", encoding="utf-8") as f:
        json.dump({"nodes": [{"event_id": "e1", "type": "db_op", "confidence": 0.8, "meta": {"path": "svc/a.py", "start_line": 3, "end_line": 3}}], "edges": []}, f)
    with open(os.path.join(rd, "api_surface.json"), "w", encoding="utf-8") as f:
        json.dump({"endpoints": [], "stats": {}, "mismatches": {}}, f)
    with open(os.path.join(rd, "entrypoints.json"), "w", encoding="utf-8") as f:
        json.dump({"entrypoints": []}, f)
    with open(os.path.join(rd, "quality_gate.json"), "w", encoding="utf-8") as f:
        json.dump({"status": "warn", "violations": []}, f)
    if with_ai:
        os.makedirs(os.path.join(rd, "ai_risks"), exist_ok=True)
        os.makedirs(os.path.join(rd, "ai_explain", "ex-1"), exist_ok=True)
        os.makedirs(os.path.join(rd, "ai_drilldown", "dd-1"), exist_ok=True)
        with open(os.path.join(rd, "ai_summary.json"), "w", encoding="utf-8") as f:
            json.dump({"project_overview": {"languages": ["python"], "frameworks": ["fastapi"], "findings": 1, "events": 1, "graph_edges": 0}, "surface_summary": {"api_count": 1, "queue_dispatch_count": 0, "db_write_count": 1}, "risk_summary": {"total_patterns": 1}, "priority_actions": [{"title": "check tx", "reason": "tx missing"}]}, f)
        with open(os.path.join(rd, "ai_risks", "risks.json"), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "risk_items": [
                        {
                            "risk_id": "risk-1",
                            "title": "Write without tx",
                            "severity": "medium",
                            "status": "suspected",
                            "pattern_type": "transaction_missing",
                            "why_it_matters": "consistency risk",
                            "recommended_action": "add tx",
                            "evidence_refs": [{"file": "svc/a.py", "start_line": 3, "end_line": 3}],
                            "snippet_refs": [{"snippet_id": "s1"}],
                            "related_patterns": ["pat-1"],
                            "learn_link": {"concept_id": "data.transaction_boundary", "href": "./learn/index.html?concept_id=data.transaction_boundary"},
                        }
                    ]
                },
                f,
            )
        with open(os.path.join(rd, "ai_explain", "ex-1", "explain.json"), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "request_id": "ex-1",
                    "target_type": "pattern",
                    "target_id": "pat-1",
                    "mode": "facts_plus_drilldown",
                    "confirmed": [{"claim": "c"}],
                    "inferred": [{"claim": "i"}],
                    "unknown": [{"question": "u"}],
                    "evidence_index": [{"file": "svc/a.py", "start_line": 3, "end_line": 3}],
                    "snippet_pack_ref": {"request_id": "dd-1"},
                },
                f,
            )
        with open(os.path.join(rd, "ai_drilldown", "dd-1", "snippet_pack.json"), "w", encoding="utf-8") as f:
            json.dump({"selected_snippets": [{"snippet_id": "s1", "file": "svc/a.py", "line_start": 1, "line_end": 4, "why_selected": "evidence_ref_window", "snippet": "def x():\n  pass"}]}, f)
    return rd
