import os
import json
import sqlite3
def run_query(run_dir, entity, as_json):
    if entity == "concepts":
        print(json.dumps(list_concepts(run_dir)) if as_json else "\n".join(list_concepts(run_dir)))
    if entity == "findings":
        items = list_findings(run_dir)
        print(json.dumps(items) if as_json else "\n".join([f'{i["fid"]} {i["concept"]} {i["confidence"]}' for i in items]))
    if entity == "evidence":
        items = list_evidence(run_dir)
        print(json.dumps(items) if as_json else "\n".join([f'{i["eid"]} {i["path"]}:{i["start_line"]}-{i["end_line"]}' for i in items]))
    if entity == "events":
        g = read_graph(run_dir)
        nodes = g.get("nodes", [])
        print(json.dumps(nodes) if as_json else "\n".join([f'{n["event_id"]} {n["type"]} {n["key"]}' for n in nodes]))
    if entity == "graph":
        g = read_graph(run_dir)
        print(json.dumps(g) if as_json else f'nodes={len(g.get("nodes", []))}, edges={len(g.get("edges", []))}')
def list_concepts(run_dir):
    conn = sqlite3.connect(os.path.join(run_dir, "detections.sqlite"))
    c = conn.cursor()
    rows = c.execute("select concept, count(*) from findings group by concept").fetchall()
    return [f"{r[0]}:{r[1]}"]
def list_findings(run_dir):
    conn = sqlite3.connect(os.path.join(run_dir, "detections.sqlite"))
    c = conn.cursor()
    rows = c.execute("select fid, concept, confidence from findings order by fid").fetchall()
    return [{"fid": r[0], "concept": r[1], "confidence": r[2]} for r in rows]
def list_evidence(run_dir):
    conn = sqlite3.connect(os.path.join(run_dir, "detections.sqlite"))
    c = conn.cursor()
    rows = c.execute("select eid, path, start_line, end_line from evidence order by eid").fetchall()
    return [{"eid": r[0], "path": r[1], "start_line": r[2], "end_line": r[3]} for r in rows]
def read_graph(run_dir):
    p = os.path.join(run_dir, "event_graph.json")
    if not os.path.exists(p):
        return {"schema_version": "1.0", "nodes": [], "edges": []}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

