import os
import json
import sqlite3
import hashlib
def _sha12(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]
def _read_graph(run_dir):
    p = os.path.join(run_dir, "event_graph.json")
    if not os.path.exists(p):
        return {"nodes": [], "edges": []}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)
def _read_report(run_dir):
    p = os.path.join(run_dir, "report.json")
    if not os.path.exists(p):
        return {"engine_version":"", "ruleset_version":"", "findings": []}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)
def _read_meta(run_dir):
    p = os.path.join(run_dir, "meta", "ruleset_version.json")
    rv = ""
    try:
        with open(p, "r", encoding="utf-8") as f:
            rv = json.load(f).get("version","")
    except:
        pass
    pv = ""
    p = os.path.join(run_dir, "meta", "tool_version.json")
    try:
        with open(p, "r", encoding="utf-8") as f:
            pv = json.load(f).get("version","")
    except:
        pass
    return {"engine_version": pv, "ruleset_version": rv}
def _load_findings_with_meta(run_dir):
    conn = sqlite3.connect(os.path.join(run_dir, "detections.sqlite"))
    c = conn.cursor()
    rows = c.execute("select f.fid, f.concept, f.rule_id, e.parse_level, f.confidence, f.primary_eid, f.meta_json from findings f join evidence e on e.eid=f.primary_eid").fetchall()
    evid = {}
    for r in c.execute("select eid, path from evidence").fetchall():
        evid[r[0]] = r[1]
    try:
        conn.close()
    except:
        pass
    items = []
    for fid, concept, rule_id, parse_level, confidence, primary_eid, meta_json in rows:
        m = {}
        try:
            m = json.loads(meta_json or "{}")
        except:
            m = {}
        items.append({
            "fid": fid,
            "concept": concept,
            "rule_id": rule_id,
            "parse_level": parse_level,
            "confidence": confidence,
            "primary_eid": primary_eid,
            "meta": m,
            "evidence_path": evid.get(primary_eid)
        })
    return items
def stable_finding_id(item):
    parts = []
    parts.append(str(item.get("concept","")))
    parts.append(str(item.get("rule_id","")))
    parts.append(str(item.get("parse_level","")))
    parts.append(str(item.get("primary_eid","")))
    meta = item.get("meta") or {}
    key_ok = False
    # API
    hm = meta.get("http.method")
    hp = meta.get("http.path")
    if hm and hp:
        parts.append(f"{hm} {hp}")
        key_ok = True
    # SQL
    tn = meta.get("table_names")
    if tn and isinstance(tn, list) and len(tn)>0:
        parts.append("|".join(sorted([str(x) for x in tn])))
        key_ok = True
    inx = meta.get("index_names")
    if inx and isinstance(inx, list) and len(inx)>0:
        parts.append("|".join(sorted([str(x) for x in inx])))
        key_ok = True
    # Compose
    svc = meta.get("service_name")
    itype = meta.get("infra_type")
    ikind = meta.get("infra_kind")
    if svc or itype or ikind:
        parts.append(str(svc or ""))
        parts.append(str(itype or ""))
        parts.append(str(ikind or ""))
        key_ok = True
    # GHA
    wpath = item.get("evidence_path")
    ik = meta.get("item_kind") or meta.get("kind")
    if wpath and ik and ".github" in (wpath or ""):
        parts.append(str(wpath))
        parts.append(str(ik))
        key_ok = True
    sid = _sha12("|".join(parts))
    return sid, key_ok
def diff_runs(runA, runB):
    gA = _read_graph(runA)
    gB = _read_graph(runB)
    nodesA = {n["event_id"]: {"event_id":n["event_id"], "type":n["type"], "key":n["key"], "confidence": n.get("confidence",0.0)} for n in gA.get("nodes", [])}
    nodesB = {n["event_id"]: {"event_id":n["event_id"], "type":n["type"], "key":n["key"], "confidence": n.get("confidence",0.0)} for n in gB.get("nodes", [])}
    edgesA = {e["edge_id"]: {"edge_id":e["edge_id"], "type":e["type"], "from":e.get("from"), "to":e.get("to")} for e in gA.get("edges", [])}
    edgesB = {e["edge_id"]: {"edge_id":e["edge_id"], "type":e["type"], "from":e.get("from"), "to":e.get("to")} for e in gB.get("edges", [])}
    ev_added = [nodesB[k] for k in sorted(set(nodesB.keys()) - set(nodesA.keys()))]
    ev_removed = [nodesA[k] for k in sorted(set(nodesA.keys()) - set(nodesB.keys()))]
    ed_added = [edgesB[k] for k in sorted(set(edgesB.keys()) - set(edgesA.keys()))]
    ed_removed = [edgesA[k] for k in sorted(set(edgesA.keys()) - set(edgesB.keys()))]
    # findings using detections.sqlite
    fA = _load_findings_with_meta(runA)
    fB = _load_findings_with_meta(runB)
    miss_count = 0
    mapA = {}
    for it in fA:
        sid, ok = stable_finding_id(it)
        if not ok:
            miss_count += 1
        mapA[sid] = {"stable_id": sid, "concept": it["concept"], "rule_id": it["rule_id"], "parse_level": it["parse_level"], "primary_eid": it["primary_eid"]}
    mapB = {}
    for it in fB:
        sid, ok = stable_finding_id(it)
        if not ok:
            miss_count += 1
        mapB[sid] = {"stable_id": sid, "concept": it["concept"], "rule_id": it["rule_id"], "parse_level": it["parse_level"], "primary_eid": it["primary_eid"]}
    fi_added = [mapB[k] for k in sorted(set(mapB.keys()) - set(mapA.keys()))]
    fi_removed = [mapA[k] for k in sorted(set(mapA.keys()) - set(mapB.keys()))]
    metaA = _read_meta(runA)
    metaB = _read_meta(runB)
    res = {
        "ok": True,
        "runA": {"path": runA, "engine_version": metaA.get("engine_version",""), "ruleset_version": metaA.get("ruleset_version","")},
        "runB": {"path": runB, "engine_version": metaB.get("engine_version",""), "ruleset_version": metaB.get("ruleset_version","")},
        "events": {"added": ev_added, "removed": ev_removed, "unchanged_count": len(set(nodesA.keys()) & set(nodesB.keys()))},
        "edges": {"added": ed_added, "removed": ed_removed, "unchanged_count": len(set(edgesA.keys()) & set(edgesB.keys()))},
        "findings": {"added": fi_added, "removed": fi_removed, "unchanged_count": len(set(mapA.keys()) & set(mapB.keys()))},
        "warnings": []
    }
    if miss_count > 0:
        res["warnings"].append({"type":"missing_key_fields","count": miss_count})
    return res
def run_diff(runA, runB, as_json):
    res = diff_runs(runA, runB)
    if as_json:
        print(json.dumps(res))
        return
    lines = []
    lines.append(f'events: +{len(res["events"]["added"])} -{len(res["events"]["removed"])} unchanged={res["events"]["unchanged_count"]}')
    lines.append(f'edges:  +{len(res["edges"]["added"])} -{len(res["edges"]["removed"])} unchanged={res["edges"]["unchanged_count"]}')
    lines.append(f'findings:+{len(res["findings"]["added"])} -{len(res["findings"]["removed"])} unchanged={res["findings"]["unchanged_count"]}')
    def top(lst, n=10):
        return lst[:n]
    lines.append("top events added:")
    for e in top(res["events"]["added"]):
        lines.append(f'- {e["event_id"]} {e["type"]} {e["key"]}')
    lines.append("top edges added:")
    for e in top(res["edges"]["added"]):
        lines.append(f'- {e["edge_id"]} {e["type"]} {e.get("from")} -> {e.get("to")}')
    lines.append("top findings added:")
    for f in top(res["findings"]["added"]):
        lines.append(f'- {f["stable_id"]} {f["concept"]} {f["parse_level"]} {f["primary_eid"]}')
    if res["warnings"]:
        lines.append("warnings:")
        for w in res["warnings"]:
            lines.append(f'- {w["type"]} count={w["count"]}')
    print("\n".join(lines))
