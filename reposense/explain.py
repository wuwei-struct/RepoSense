import os
import json
import sqlite3
def explain_event(run_dir, event_hash_id, as_json):
    with open(os.path.join(run_dir, "event_graph.json"), "r", encoding="utf-8") as f:
        graph = json.load(f)
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node = next((n for n in nodes if n.get("event_id") == event_hash_id), None)
    if not node:
        out = {"error": "event not found"}
        return out if as_json else "error=event not found"
    conn = sqlite3.connect(os.path.join(run_dir, "detections.sqlite"))
    c = conn.cursor()
    ev_items = []
    for ev in node.get("evidence", []):
        try:
            eid = int(ev[1:])
        except:
            continue
        r = c.execute("select path, start_line, end_line, snippet, parse_level from evidence where eid=?", (eid,)).fetchone()
        if r:
            ev_items.append({"eid": ev, "path": r[0], "start_line": r[1], "end_line": r[2], "snippet": r[3], "level": r[4]})
    incoming = []
    outgoing = []
    for e in edges:
        if e.get("type") == "declares_dependency" and e.get("to") == event_hash_id:
            src = next((n for n in nodes if n.get("event_id") == e.get("from")), None)
            if src:
                incoming.append({"event_id": src["event_id"], "type": src["type"], "key": src["key"]})
        if e.get("type") == "declares_dependency" and e.get("from") == event_hash_id:
            dst = next((n for n in nodes if n.get("event_id") == e.get("to")), None)
            if dst:
                outgoing.append({"event_id": dst["event_id"], "type": dst["type"], "key": dst["key"]})
    try:
        conn.close()
    except:
        pass
    res = {
        "summary": {"type": node["type"], "key": node["key"], "confidence": node.get("confidence"), "source": (node.get("meta") or {}).get("source")},
        "evidence": ev_items,
        "neighbors": {"incoming_declares_dependency": incoming, "outgoing_declares_dependency": outgoing}
    }
    if as_json:
        return res
    lines = []
    s = res["summary"]
    lines.append(f'event {event_hash_id} type={s["type"]} key={s["key"]} confidence={s["confidence"]} source={s.get("source")}')
    lines.append("evidence:")
    for e in res["evidence"]:
        lines.append(f'- {e["eid"]} {e["path"]}:{e["start_line"]}-{e["end_line"]} [{e["level"]}]')
        lines.append(f'  {e["snippet"]}')
    lines.append("incoming_declares_dependency:")
    for n in incoming:
        lines.append(f'- {n["event_id"]} {n["type"]} {n["key"]}')
    lines.append("outgoing_declares_dependency:")
    for n in outgoing:
        lines.append(f'- {n["event_id"]} {n["type"]} {n["key"]}')
    return "\n".join(lines)
def explain_finding(run_dir, fid, as_json):
    conn = sqlite3.connect(os.path.join(run_dir, "detections.sqlite"))
    c = conn.cursor()
    row = c.execute("select concept, rule_id, confidence, primary_eid, meta_json from findings where fid=?", (fid,)).fetchone()
    if not row:
        out = {"error": "finding not found"}
        try:
            conn.close()
        except:
            pass
        return out if as_json else "error=finding not found"
    concept, rule_id, confidence, primary_eid, meta_json = row
    ev_rows = c.execute("select e.eid, e.path, e.start_line, e.end_line, e.snippet, e.parse_level from evidence e join finding_evidence fe on fe.eid=e.eid where fe.fid=?", (fid,)).fetchall()
    if not ev_rows:
        # include primary evidence at minimum
        r = c.execute("select eid, path, start_line, end_line, snippet, parse_level from evidence where eid=?", (primary_eid,)).fetchone()
        ev_rows = [r] if r else []
    try:
        conn.close()
    except:
        pass
    ev_items = [{"eid": f"E{r[0]}", "path": r[1], "start_line": r[2], "end_line": r[3], "snippet": r[4], "level": r[5]} for r in ev_rows]
    meta = {}
    try:
        meta = json.loads(meta_json or "{}")
    except:
        meta = {}
    res = {"summary": {"fid": fid, "concept": concept, "rule_id": rule_id, "confidence": confidence, "markers_hit": meta.get("markers_hit"), "anti_patterns_hit": meta.get("anti_patterns_hit"), "score": meta.get("score")}, "evidence": ev_items}
    if as_json:
        return res
    lines = []
    s = res["summary"]
    lines.append(f'finding {s["fid"]} concept={s["concept"]} rule_id={s["rule_id"]} confidence={s["confidence"]} score={s.get("score")}')
    if s.get("markers_hit") is not None:
        lines.append("markers_hit: " + ", ".join(s["markers_hit"]))
    if s.get("anti_patterns_hit") is not None:
        lines.append("anti_patterns_hit: " + ", ".join(s["anti_patterns_hit"]))
    lines.append("evidence:")
    for e in ev_items:
        lines.append(f'- {e["eid"]} {e["path"]}:{e["start_line"]}-{e["end_line"]} [{e["level"]}]')
        lines.append(f'  {e["snippet"]}')
    return "\n".join(lines)
def run_explain(run_dir, subject, id_, as_json):
    if subject == "event":
        out = explain_event(run_dir, id_, as_json)
        print(json.dumps(out) if as_json else out)
    elif subject == "finding":
        try:
            fid = int(id_)
        except:
            print("error=invalid fid")
            return
        out = explain_finding(run_dir, fid, as_json)
        print(json.dumps(out) if as_json else out)
