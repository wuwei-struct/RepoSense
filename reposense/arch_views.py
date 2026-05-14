import os
import json
import sqlite3
from pathlib import Path
def _read_graph(run_dir):
    p = Path(run_dir) / "event_graph.json"
    if not p.exists():
        return {"nodes": [], "edges": []}
    return json.load(open(p, "r", encoding="utf-8"))
def _open_db(run_dir):
    conn = sqlite3.connect(str(Path(run_dir) / "detections.sqlite"))
    conn.row_factory = sqlite3.Row
    return conn
def _evidence_path(conn, eid):
    try:
        r = conn.cursor().execute("select path from evidence where eid=?", (eid,)).fetchone()
        return r["path"] if r else ""
    except:
        return ""
def _evidence_exists(run_dir, eid):
    return Path(run_dir).joinpath("evidence", f"E{eid}.json").exists()
def _normalize_eids(eids):
    out = []
    for ev in sorted(set(eids)):
        try:
            if isinstance(ev, str) and ev.startswith("E"):
                out.append(int(ev[1:]))
            else:
                out.append(int(ev))
        except:
            pass
    return sorted(out)
def build_arch_views(run_dir, out_dir=None):
    outp = Path(out_dir or (Path(run_dir) / "arch_views")).resolve()
    outp.mkdir(parents=True, exist_ok=True)
    g = _read_graph(run_dir)
    conn = _open_db(run_dir)
    # api_surface
    apis = []
    for n in g.get("nodes", []):
        if n.get("type") == "api":
            eids = _normalize_eids(n.get("evidence", []))
            first_path = _evidence_path(conn, eids[0]) if eids else ""
            apis.append({
                "id": n["event_id"],
                "type": "api",
                "method": (n.get("key","").split(" ")[0] if n.get("key") else ""),
                "path": (" ".join(n.get("key","").split(" ")[1:]) if n.get("key") else ""),
                "key": n.get("key"),
                "confidence": n.get("confidence", 0.0),
                "source": (n.get("meta") or {}).get("source"),
                "evidence": [f"E{eid}" for eid in eids],
                "module_hint": os.path.dirname(first_path) if first_path else ""
            })
    apis = sorted(apis, key=lambda x: (x["method"], x["path"]))
    (outp / "api_surface.json").write_text(json.dumps({"items": apis}), encoding="utf-8")
    # service_map
    services = []
    infra = []
    edges = []
    svc_index = {}
    infra_index = {}
    for n in g.get("nodes", []):
        t = n.get("type")
        if t == "service":
            eids = _normalize_eids(n.get("evidence", []))
            compose_path = _evidence_path(conn, eids[0]) if eids else ""
            services.append({
                "id": n["event_id"],
                "service_name": n.get("key","service:").split("service:",1)[-1],
                "evidence": [f"E{eid}" for eid in eids],
                "compose_path": compose_path,
                "module_hint": os.path.dirname(compose_path) if compose_path else ""
            })
            svc_index[n["event_id"]] = services[-1]
        if t in ["cache","queue","storage"]:
            eids = _normalize_eids(n.get("evidence", []))
            infra.append({
                "id": n["event_id"],
                "infra_type": t,
                "infra_kind": n.get("key", f"{t}:").split(f"{t}:",1)[-1],
                "key": n.get("key"),
                "evidence": [f"E{eid}" for eid in eids]
            })
            infra_index[n["event_id"]] = infra[-1]
    for e in g.get("edges", []):
        if e.get("type") == "declares_dependency":
            src = e.get("from")
            dst = e.get("to")
            if src in svc_index and dst in infra_index:
                eids = _normalize_eids(e.get("evidence", []))
                edges.append({
                    "from": src,
                    "to": dst,
                    "type": "declares_dependency",
                    "evidence": [f"E{eid}" for eid in eids]
                })
    edges = sorted(edges, key=lambda x: (x["from"], x["to"]))
    (outp / "service_map.json").write_text(json.dumps({"services": sorted(services, key=lambda x: x["service_name"]), "infra": sorted(infra, key=lambda x: (x["infra_type"], x["infra_kind"])), "edges": edges}), encoding="utf-8")
    # data_surface
    tables = []
    indexes = []
    for n in g.get("nodes", []):
        if n.get("type") in ["table","index"]:
            eids = _normalize_eids(n.get("evidence", []))
            first_path = _evidence_path(conn, eids[0]) if eids else ""
            item = {
                "name": n.get("key", "").split(":",1)[-1],
                "key": n.get("key"),
                "evidence": [f"E{eid}" for eid in eids],
                "module_hint": os.path.dirname(first_path) if first_path else ""
            }
            if n.get("type") == "table":
                tables.append(item)
            else:
                indexes.append(item)
    (outp / "data_surface.json").write_text(json.dumps({"tables": sorted(tables, key=lambda x: x["name"]), "indexes": sorted(indexes, key=lambda x: x["name"])}), encoding="utf-8")
    # async_surface
    workflows = []
    schedulers = []
    queues = []
    for n in g.get("nodes", []):
        if n.get("type") == "workflow":
            eids = _normalize_eids(n.get("evidence", []))
            workflows.append({
                "workflow_path": n.get("key","workflow:").split("workflow:",1)[-1],
                "evidence": [f"E{eid}" for eid in eids]
            })
        if n.get("type") == "workflow_item":
            eids = _normalize_eids(n.get("evidence", []))
            schedulers.append({
                "kind": n.get("key"),
                "evidence": [f"E{eid}" for eid in eids]
            })
        if n.get("type") == "queue":
            eids = _normalize_eids(n.get("evidence", []))
            queues.append({
                "infra_type": "queue",
                "infra_kind": n.get("key","queue:").split("queue:",1)[-1],
                "evidence": [f"E{eid}" for eid in eids]
            })
    (outp / "async_surface.json").write_text(json.dumps({"workflows": sorted(workflows, key=lambda x:x["workflow_path"]), "schedulers": sorted(schedulers, key=lambda x:x["kind"]), "queues": sorted(queues, key=lambda x:x["infra_kind"])}), encoding="utf-8")
    # deps_surface
    deps = []
    # compose infra already covered; also External IO findings
    rows = conn.cursor().execute("select f.fid, f.concept, f.primary_eid from findings f").fetchall()
    ext_eids = []
    for r in rows:
        if r["concept"] == "External IO":
            try:
                ext_eids.append(int(r["primary_eid"]))
            except:
                pass
    if ext_eids:
        for eid in sorted(ext_eids):
            deps.append({"dep_type": "external_io", "dep_kind": "", "evidence": [f"E{eid}"], "where_used": [_evidence_path(conn, eid)]})
    # also include infra nodes as deps
    for n in g.get("nodes", []):
        if n.get("type") in ["cache","queue","storage"]:
            eids = _normalize_eids(n.get("evidence", []))
            deps.append({"dep_type": n.get("type"), "dep_kind": n.get("key","").split(":",1)[-1], "evidence": [f"E{eid}" for eid in eids], "where_used": []})
    (outp / "deps_surface.json").write_text(json.dumps({"deps": sorted(deps, key=lambda x:(x["dep_type"], x["dep_kind"]))}), encoding="utf-8")
    # warnings file placeholder
    (outp / "_warnings.json").write_text(json.dumps([]), encoding="utf-8")
    try:
        conn.close()
    except:
        pass
    return str(outp)
