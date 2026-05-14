import os
import json
import sqlite3
import hashlib
from .utils import write_json
def _sha12(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]
def _node(type_, key, confidence, evidence_ids, meta):
    return {"event_id": _sha12(f"{type_}:{key}"), "type": type_, "key": key, "confidence": float(confidence), "evidence": [f"E{eid}" for eid in sorted(set(evidence_ids))], "meta": meta or {}}
def _edge_supported_by(from_event_id, eid):
    eids = [eid]
    edge_id = _sha12(f"{from_event_id}:E{eid}:supported_by:{','.join([str(x) for x in eids])}")
    return {"edge_id": edge_id, "type": "supported_by", "from": from_event_id, "to": f"E{eid}", "evidence": [f"E{eid}"], "meta": {}}
def _edge_declares(src_event_id, dst_event_id, eids):
    edge_id = _sha12(f"{src_event_id}:{dst_event_id}:declares:{','.join(sorted([str(x) for x in eids]))}")
    return {"edge_id": edge_id, "type": "declares", "from": src_event_id, "to": dst_event_id, "evidence": [f"E{eid}" for eid in sorted(set(eids))], "meta": {}}
def _edge_observed_same_scope(src_event_id, dst_event_id, eids):
    edge_id = _sha12(f"{src_event_id}:{dst_event_id}:observed_in_same_scope:{','.join(sorted([str(x) for x in eids]))}")
    return {"edge_id": edge_id, "type": "observed_in_same_scope", "from": src_event_id, "to": dst_event_id, "evidence": [f"E{eid}" for eid in sorted(set(eids))], "meta": {}}
def _edge_semantic(src_event_id, dst_event_id, kind, eids, meta):
    edge_id = _sha12(f"{src_event_id}:{dst_event_id}:{kind}:{','.join(sorted([str(x) for x in eids]))}")
    m = meta or {}
    return {"edge_id": edge_id, "type": kind, "from": src_event_id, "to": dst_event_id, "evidence": [f"E{eid}" for eid in sorted(set(eids))], "meta": m}
def build_graph(run_dir):
    det_path = os.path.join(run_dir, "detections.sqlite")
    with open(os.path.join(run_dir, "manifest.json"), "r", encoding="utf-8") as mf:
        man = json.load(mf)
    repo_root = man.get("repo_root", "")
    conn = sqlite3.connect(det_path)
    c = conn.cursor()
    rows = c.execute("select f.fid, f.concept, f.confidence, f.primary_eid, f.meta_json, e.path, e.start_line, e.end_line, e.parse_level, e.snippet from findings f join evidence e on e.eid=f.primary_eid").fetchall()
    nodes = {}
    edges = []
    def _rel(p):
        try:
            return os.path.relpath(p, repo_root).replace("\\", "/")
        except Exception:
            return p.replace("\\", "/")
    for fid, concept, conf, eid, meta_json, path, start_line, end_line, level, snip in rows:
        if concept == "API":
            m = {}
            try:
                m = json.loads(meta_json or "{}")
            except:
                m = {}
            method = m.get("http.method")
            pth = m.get("http.path")
            if not method or not pth:
                parts = snip.strip().split()
                if len(parts) >= 2:
                    method = parts[0].upper()
                    pth = parts[1]
            if method and pth:
                key = f"{method} {pth}"
                k = ("api", key)
                src = m.get("evidence_strength") or ("ast" if level == "L3" else "openapi")
                meta = {"source": src}
                if m.get("scope"):
                    meta["scope"] = m.get("scope")
                meta["path"] = _rel(path)
                if m.get("language"):
                    meta["language"] = m.get("language")
                if m.get("framework"):
                    meta["framework"] = m.get("framework")
                meta["parse_level"] = m.get("parse_level") or level
                n = nodes.get(k)
                if not n:
                    nodes[k] = _node("api", key, conf, [eid], meta)
                else:
                    n["confidence"] = max(n["confidence"], float(conf))
                    n["evidence"].append(f"E{eid}")
                edges.append(_edge_supported_by(nodes[k]["event_id"], eid))
    typed = []
    for fid, concept, conf, eid, meta_json, path, start_line, end_line, level, snip in rows:
        m = {}
        try:
            m = json.loads(meta_json or "{}")
        except Exception:
            m = {}
        pk = m.get("python.kind")
        tsk = m.get("ts.kind")
        scope = m.get("scope") or {}
        scope_key = f'{scope.get("kind","module")}:{scope.get("name","")}'
        rel = _rel(path)
        txk = m.get("tx.kind")
        if concept == "Transaction" and (pk == "django_atomic" or txk in ("django_atomic", "sql_begin_commit", "ts_prisma_transaction", "ts_typeorm_transaction", "java_transactional")):
            kind = m.get("tx.kind") or "django_atomic"
            key = f"{rel}:{scope_key}:{kind}:{int(start_line or 0)}-{int(end_line or 0)}"
            k = ("tx_boundary", key)
            src = "python_ast" if pk == "django_atomic" else (m.get("evidence_strength") or "text")
            meta = {"source": src, "tx.kind": kind, "scope": scope, "path": rel}
            if m.get("language"):
                meta["language"] = m.get("language")
            if m.get("framework"):
                meta["framework"] = m.get("framework")
            if m.get("transaction_style"):
                meta["transaction_style"] = m.get("transaction_style")
            if m.get("callee_expr"):
                meta["callee_expr"] = m.get("callee_expr")
            meta["parse_level"] = m.get("parse_level") or level
            if k not in nodes:
                nodes[k] = _node("tx_boundary", key, conf, [eid], meta)
            edges.append(_edge_supported_by(nodes[k]["event_id"], eid))
            typed.append((path, scope, eid, nodes[k]["event_id"]))
        jk = str(m.get("java.kind") or "")
        is_java_queue = jk in ("queue_dispatch", "queue_consume")
        if concept == "Queue" and (pk == "celery_dispatch" or tsk in ("queue_dispatch", "queue_consume") or is_java_queue):
            is_consume = (tsk == "queue_consume") or (jk == "queue_consume")
            qk = m.get("queue.kind") or ("ts_queue_consume" if is_consume else "celery_dispatch")
            task = m.get("queue.task") or ""
            key = f"{rel}:{scope_key}:{qk}:{task}:{int(start_line or 0)}"
            node_type = "queue_consume" if is_consume else "queue_dispatch"
            src = "python_ast" if pk == "celery_dispatch" else (m.get("evidence_strength") or ("java_l2" if is_java_queue else "typescript_l2"))
            meta = {"source": src, "queue.kind": qk, "queue.task": task, "scope": scope, "path": rel}
            if m.get("language"):
                meta["language"] = m.get("language")
            if m.get("framework"):
                meta["framework"] = m.get("framework")
            if m.get("queue_name"):
                meta["queue_name"] = m.get("queue_name")
            if m.get("topic_name"):
                meta["topic_name"] = m.get("topic_name")
            if m.get("queue.system"):
                meta["queue.system"] = m.get("queue.system")
            if m.get("job_name"):
                meta["job_name"] = m.get("job_name")
            if m.get("consumer_style"):
                meta["consumer_style"] = m.get("consumer_style")
            if m.get("callee_expr"):
                meta["callee_expr"] = m.get("callee_expr")
            meta["parse_level"] = m.get("parse_level") or level
            k = (node_type, key)
            if k not in nodes:
                nodes[k] = _node(node_type, key, conf, [eid], meta)
            edges.append(_edge_supported_by(nodes[k]["event_id"], eid))
            typed.append((path, scope, eid, nodes[k]["event_id"]))
        if concept == "DB":
            op = str(m.get("db.op") or "")
            dstyle = str(m.get("db_style") or "")
            key = f"{rel}:{scope_key}:{dstyle}:{op}:{int(start_line or 0)}"
            k = ("db_op", key)
            src = m.get("evidence_strength") or "java_l2"
            meta = {"source": src, "db.op": op, "db_style": dstyle, "scope": scope, "path": rel}
            if m.get("db.kind"):
                meta["db.kind"] = m.get("db.kind")
            if m.get("repo_symbol"):
                meta["repo_symbol"] = m.get("repo_symbol")
            if m.get("mapper_symbol"):
                meta["mapper_symbol"] = m.get("mapper_symbol")
            if m.get("statement_hint"):
                meta["statement_hint"] = m.get("statement_hint")
            if m.get("entity_hint"):
                meta["entity_hint"] = m.get("entity_hint")
            if m.get("callee_expr"):
                meta["callee_expr"] = m.get("callee_expr")
            if m.get("language"):
                meta["language"] = m.get("language")
            if m.get("framework"):
                meta["framework"] = m.get("framework")
            meta["parse_level"] = m.get("parse_level") or level
            if k not in nodes:
                nodes[k] = _node("db_op", key, conf, [eid], meta)
            edges.append(_edge_supported_by(nodes[k]["event_id"], eid))
            typed.append((path, scope, eid, nodes[k]["event_id"]))
        if concept == "Cache" and (pk in ("django_cache_op", "redis_op") or tsk == "cache_op"):
            backend = m.get("cache.backend") or ("django_cache" if pk == "django_cache_op" else "redis")
            op = m.get("cache.op") or ""
            key = f"{rel}:{scope_key}:{backend}:{op}:{int(start_line or 0)}"
            k = ("cache_op", key)
            src = "python_ast" if pk in ("django_cache_op", "redis_op") else (m.get("evidence_strength") or "typescript_l2")
            meta = {"source": src, "cache.backend": backend, "cache.op": op, "scope": scope, "path": rel}
            if m.get("cache.kind"):
                meta["cache.kind"] = m.get("cache.kind")
            if m.get("key_literal"):
                meta["key_literal"] = m.get("key_literal")
            if m.get("key_expr"):
                meta["key_expr"] = m.get("key_expr")
            if m.get("callee_expr"):
                meta["callee_expr"] = m.get("callee_expr")
            if m.get("language"):
                meta["language"] = m.get("language")
            if m.get("framework"):
                meta["framework"] = m.get("framework")
            meta["parse_level"] = m.get("parse_level") or level
            if k not in nodes:
                nodes[k] = _node("cache_op", key, conf, [eid], meta)
            edges.append(_edge_supported_by(nodes[k]["event_id"], eid))
            typed.append((path, scope, eid, nodes[k]["event_id"]))
    api_evs = []
    for fid, concept, conf, eid, meta_json, path, start_line, end_line, level, snip in rows:
        if concept != "API":
            continue
        try:
            m = json.loads(meta_json or "{}")
        except Exception:
            m = {}
        scope = m.get("scope") or {}
        method = (m.get("http.method") or "").upper()
        pth = m.get("http.path")
        if method and pth:
            key = f"{method} {pth}"
            api_evs.append((path, scope, eid, nodes[("api", key)]["event_id"]))
    for p, sc_api, eid_api, api_id in api_evs:
        used_pairs = set()
        for p2, sc2, eid2, dst_id in typed:
            if p != p2:
                continue
            ok = False
            if sc_api.get("kind") == sc2.get("kind") == "function":
                if sc_api.get("name") and sc_api.get("name") == sc2.get("name"):
                    ok = True
            if not ok:
                try:
                    a1, a2 = int(sc_api.get("start_line") or 0), int(sc_api.get("end_line") or 0)
                    b1, b2 = int(sc2.get("start_line") or 0), int(sc2.get("end_line") or 0)
                    if a1 and a2 and b1 and b2 and (b1 >= a1 and b2 <= a2):
                        ok = True
                except Exception:
                    ok = False
            if ok:
                # build semantic edge based on dst type
                src_sid = f'py:function:{sc_api.get("name","")}@{int(sc_api.get("start_line") or 0)}:{int(sc_api.get("end_line") or 0)}'
                dst_sid = f'py:function:{sc2.get("name","")}@{int(sc2.get("start_line") or 0)}:{int(sc2.get("end_line") or 0)}'
                span_lines = max(0, int(sc2.get("end_line") or 0) - int(sc2.get("start_line") or 0) + 1)
                base_meta = {"confidence": 0.9, "reason": "same_file_same_function_and_contained", "scope_id": src_sid, "span_overlap": {"contained": True, "lines": span_lines}}
                # determine kind by dst node type
                kind_map = {"tx_boundary": "encloses_tx", "cache_op": "uses_cache", "queue_dispatch": "dispatches_job"}
                # find dst node type by looking up node by event_id
                dst_node = next((n for n in nodes.values() if n["event_id"] == dst_id), None)
                dst_type = dst_node["type"] if dst_node else None
                k = kind_map.get(dst_type)
                if k:
                    key_pair = (api_id, dst_id, k)
                    if key_pair not in used_pairs:
                        edges.append(_edge_semantic(api_id, dst_id, k, [eid_api, eid2], base_meta))
                        used_pairs.add(key_pair)
                # always include observed_in_same_scope to preserve legacy visibility
                edges.append(_edge_observed_same_scope(api_id, dst_id, [eid_api, eid2]))
    gha_paths = [r[5] for r in rows if r[5].replace("\\","/").find(".github/workflows/") != -1]
    for wf_path in sorted(set(gha_paths)):
        rel = os.path.relpath(wf_path, repo_root).replace("\\","/")
        key = f"workflow:{rel}"
        k = ("workflow", key)
        wf_eids = [r[3] for r in rows if r[5] == wf_path]
        meta = {"source": "gha"}
        nodes[k] = _node("workflow", key, 0.6, wf_eids, meta)
        for eid in wf_eids:
            edges.append(_edge_supported_by(nodes[k]["event_id"], eid))
        kinds = []
        for r in rows:
            if r[5] == wf_path and r[1] in ["Scheduling","Cache","Concurrency"]:
                kinds.append(r[1])
        for kind in sorted(set(kinds)):
            item_key = f"{kind.lower()}"
            child = _node("workflow_item", item_key, 0.6, [e for e in wf_eids], {"source":"gha"})
            nodes[("workflow_item", item_key)] = child
            edges.append(_edge_declares(nodes[k]["event_id"], child["event_id"], wf_eids))
    for fid, concept, conf, eid, meta_json, path, start_line, end_line, level, snip in rows:
        if concept in ["Storage","Index"]:
            try:
                m = json.loads(meta_json or "{}")
            except:
                m = {}
            if concept == "Storage":
                for name in m.get("table_names", []):
                    key = f"table:{name}"
                    k = ("table", key)
                    meta = {"source": "sql_ddl"}
                    n = nodes.get(k)
                    if not n:
                        nodes[k] = _node("table", key, conf, [eid], meta)
                    else:
                        n["confidence"] = max(n["confidence"], float(conf))
                        n["evidence"].append(f"E{eid}")
                    edges.append(_edge_supported_by(nodes[k]["event_id"], eid))
            if concept == "Index":
                for name in m.get("index_names", []):
                    key = f"index:{name}"
                    k = ("index", key)
                    meta = {"source": "sql_ddl"}
                    n = nodes.get(k)
                    if not n:
                        nodes[k] = _node("index", key, conf, [eid], meta)
                    else:
                        n["confidence"] = max(n["confidence"], float(conf))
                        n["evidence"].append(f"E{eid}")
                    edges.append(_edge_supported_by(nodes[k]["event_id"], eid))
    compose_rows = []
    for fid, concept, conf, eid, meta_json, path, start_line, end_line, level, snip in rows:
        if concept in ["KV/Storage","Queue","Cache","External IO"]:
            try:
                m = json.loads(meta_json or "{}")
            except:
                m = {}
            svc = m.get("service_name")
            ikind = m.get("infra_kind")
            itype = m.get("infra_type")
            compose_rows.append((svc, itype, ikind, eid, conf, path, concept))
    for svc in sorted(set([r[0] for r in compose_rows if r[0]])):
        key = f"service:{svc}"
        k = ("service", key)
        eids = [r[3] for r in compose_rows if r[0] == svc]
        nodes[k] = _node("service", key, 0.6, eids, {"source":"compose"})
        for eid in eids:
            edges.append(_edge_supported_by(nodes[k]["event_id"], eid))
    for svc, itype, ikind, eid, conf, path, concept in compose_rows:
        if itype and ikind and svc:
            key = f"{itype}:{ikind}"
            k = (itype, key)
            meta = {"source": "compose"}
            n = nodes.get(k)
            if not n:
                nodes[k] = _node(itype, key, 0.6, [eid], meta)
            else:
                n["evidence"].append(f"E{eid}")
            edges.append(_edge_supported_by(nodes[k]["event_id"], eid))
            src_id = nodes[("service", f"service:{svc}")]["event_id"]
            dst_id = nodes[(itype, key)]["event_id"]
            dep = _edge_declares(src_id, dst_id, [eid])
            dep["type"] = "declares_dependency"
            edges.append(dep)
    try:
        with open(os.path.join(run_dir, "meta", "config.json"), "r", encoding="utf-8") as _cfgf:
            cfg = json.load(_cfgf)
        rsdir = cfg.get("ruleset_dir") or ""
        from .versioning import ruleset_fingerprint, generated_by
        rid = os.path.basename(rsdir) if rsdir else ""
        rfp = ruleset_fingerprint(rsdir) if rsdir and os.path.isdir(rsdir) else ""
        gb = generated_by("0.1.0", rid, rfp, 1)
    except Exception:
        gb = {"tool":"reposense","reposense_version":"0.1.0","ruleset_id":"","ruleset_fingerprint":"","schema_version":1}
    # tx -> cache/queue semantic edges within tx span
    def _span(sc):
        return (int((sc or {}).get("start_line") or 0), int((sc or {}).get("end_line") or 0))
    tx_nodes = [n for n in nodes.values() if n["type"] == "tx_boundary"]
    cache_nodes = [n for n in nodes.values() if n["type"] == "cache_op"]
    queue_nodes = [n for n in nodes.values() if n["type"] == "queue_dispatch"]
    pair_set = set()
    for tx in tx_nodes:
        tpath = tx["meta"].get("path")
        ts, te = _span(tx["meta"].get("scope"))
        for ca in cache_nodes:
            if ca["meta"].get("path") != tpath:
                continue
            cs, ce = _span(ca["meta"].get("scope"))
            if ts and te and cs and ce and (cs >= ts and ce <= te):
                k = ("cache_within_tx", tx["event_id"], ca["event_id"])
                if k not in pair_set:
                    m = {"confidence": 0.9, "reason": "same_file_same_function_and_contained", "scope_id": f'py:function:{(tx["meta"].get("scope") or {}).get("name","")}@{ts}:{te}', "span_overlap": {"contained": True, "lines": max(0, ce-cs+1)}}
                    edges.append(_edge_semantic(tx["event_id"], ca["event_id"], "cache_within_tx", [], m))
                    pair_set.add(k)
        for qu in queue_nodes:
            if qu["meta"].get("path") != tpath:
                continue
            qs, qe = _span(qu["meta"].get("scope"))
            if ts and te and qs and qe and (qs >= ts and qe <= te):
                k = ("dispatch_within_tx", tx["event_id"], qu["event_id"])
                if k not in pair_set:
                    m = {"confidence": 0.9, "reason": "same_file_same_function_and_contained", "scope_id": f'py:function:{(tx["meta"].get("scope") or {}).get("name","")}@{ts}:{te}', "span_overlap": {"contained": True, "lines": max(0, qe-qs+1)}}
                    edges.append(_edge_semantic(tx["event_id"], qu["event_id"], "dispatch_within_tx", [], m))
                    pair_set.add(k)
    graph = {"schema_version": 1, "nodes": sorted(list(nodes.values()), key=lambda x: x.get("event_id")), "edges": sorted(edges, key=lambda x: x.get("edge_id")), "generated_by": gb}
    write_json(os.path.join(run_dir, "event_graph.json"), graph)
    cur_events = c.execute("select event_id, type, key from events").fetchall()
    map_id = {(r[1], r[2]): r[0] for r in cur_events}
    for n in graph["nodes"]:
        if (n["type"], n["key"]) in map_id:
            continue
        meta_obj = {"evidence_refs": n.get("evidence") or []}
        if n.get("meta"):
            meta_obj.update(n.get("meta") or {})
        c.execute("insert into events(type, key, confidence, meta_json) values(?,?,?,?)", (n["type"], n["key"], n.get("confidence", 0), json.dumps(meta_obj)))
        map_id[(n["type"], n["key"])] = c.lastrowid
    conn.commit()
    for e in graph["edges"]:
        if e["type"] in ["declares","declares_dependency","observed_in_same_scope"]:
            src = e["from"]
            dst = e["to"]
            src_node = next((n for n in graph["nodes"] if n["event_id"] == src), None)
            dst_node = next((n for n in graph["nodes"] if n["event_id"] == dst), None)
            if src_node and dst_node:
                c.execute("insert into event_links(src_event, dst_event, kind) values(?,?,?)", (map_id.get((src_node["type"], src_node["key"])), map_id.get((dst_node["type"], dst_node["key"])), e["type"]))
    conn.commit()
    try:
        conn.close()
    except:
        pass
    return graph
