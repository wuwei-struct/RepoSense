import os
import json
from .importers import import_input
from .scanner import walk_files_with_stats, collect_file_info
from .sqlite_store import init_indices_db, init_detections_db, insert_file, insert_text_hit, insert_evidence, insert_finding, link_finding_evidence, insert_event
from .rules import load_ruleset
from .detectors import run_detectors
from .packager import make_run_dir, write_manifest, write_meta, write_event_graph, write_report_json, write_evidence_json, write_coverage
from .graph_builder import build_graph
from .context_pack import build_context_pack, zip_context_pack
from .api_surface import build_api_surface
from .entrypoints import build_entrypoints
from .utils import now_millis, sha256_file
from .report import build_report_html
from .events.normalize import collect_detected_languages_frameworks
from .adapters.registry import list_registered_languages
from .language_capabilities import build_language_capabilities
from .cross_language import build_cross_language_exports
from .analysis.ai.pattern_export import export_patterns
def run_scan(input_path, out_dir, ruleset_dir, budget_path, base_run_dir=None, specs_dir=None):
    with open(budget_path, "r", encoding="utf-8") as f:
        budget = json.load(f)
    repo_root = import_input(input_path, out_dir, budget)
    run_dir = make_run_dir(out_dir, repo_root)
    idx_path = os.path.join(run_dir, "indices.sqlite")
    det_path = os.path.join(run_dir, "detections.sqlite")
    if os.path.exists(idx_path):
        try:
            os.remove(idx_path)
        except Exception:
            pass
    if os.path.exists(det_path):
        try:
            os.remove(det_path)
        except Exception:
            pass
    ruleset = load_ruleset(ruleset_dir)
    from .versioning import ruleset_fingerprint, generated_by
    rs_fp = ""
    try:
        rs_fp = ruleset_fingerprint(ruleset_dir)
    except Exception:
        rs_fp = ""
    manifest = {"repo_root": os.path.abspath(repo_root), "timestamp": now_millis()}
    write_manifest(run_dir, manifest)
    extra_meta = {"budget": budget, "budget_path": budget_path, "ruleset_dir": ruleset_dir}
    if base_run_dir:
        extra_meta["incremental"] = {"base_run_dir": base_run_dir, "skipped_count": 0}
    # optional specs fingerprint
    if specs_dir:
        try:
            from .specs import fingerprint_specs
            extra_meta["specs_fingerprint"] = fingerprint_specs(specs_dir)
        except Exception as e:
            extra_meta.setdefault("warnings", []).append("specs_fingerprint_failed")
    write_meta(run_dir, {"version": "0.1.0"}, ruleset["version"], extra_meta)
    raw_files, walk_stats = walk_files_with_stats(repo_root, budget)
    files = [collect_file_info(p) for p in raw_files]
    try:
        import hashlib
        h = hashlib.sha256()
        for fi in sorted(files, key=lambda x: x["path"]):
            rel = os.path.relpath(fi["path"], repo_root).replace("\\", "/")
            h.update((rel + ":" + fi["sha256"] + "\n").encode("utf-8"))
        content_id = h.hexdigest()
    except Exception:
        content_id = None
    try:
        import hashlib
        h2 = hashlib.sha256()
        h2.update((content_id or "").encode("utf-8"))
        h2.update(json.dumps(budget, sort_keys=True).encode("utf-8"))
        h2.update(json.dumps(ruleset["version"], sort_keys=True).encode("utf-8"))
        pack_id = h2.hexdigest()
    except Exception:
        pack_id = None
    idx_db = init_indices_db(os.path.join(run_dir, "indices.sqlite"))
    for fi in files:
        insert_file(idx_db, fi)
    detections_db = init_detections_db(os.path.join(run_dir, "detections.sqlite"))
    results, warnings = run_detectors(ruleset, files, budget) if not base_run_dir else ([], [])
    skipped = 0
    base_ev = None
    base_find = None
    events = []
    report_findings = []
    inserted_events = set()
    if base_run_dir:
        import sqlite3
        base_ev = sqlite3.connect(os.path.join(base_run_dir, "detections.sqlite"))
        base_c = base_ev.cursor()
        base_rows = base_c.execute("select eid, path, start_line, end_line, snippet, sha256, parse_level from evidence").fetchall()
        base_map = {}
        # key by relative path to base repo_root
        with open(os.path.join(base_run_dir, "manifest.json"), "r", encoding="utf-8") as f:
            base_manifest = json.load(f)
        base_root = base_manifest.get("repo_root","")
        for r in base_rows:
            rel = os.path.relpath(r[1], base_root).replace("\\","/")
            base_map.setdefault(rel, []).append(r)
        # reuse when sha256 unchanged
        for fi in files:
            sha = sha256_file(fi["path"])
            rel_cur = os.path.relpath(fi["path"], repo_root).replace("\\","/")
            prevs = base_map.get(rel_cur, [])
            unchanged = any(r[5] == sha for r in prevs)
            if unchanged:
                skipped += 1
                # copy findings/evidence from base for this path
                abs_in_base = os.path.join(base_root, rel_cur).replace("\\","/")
                base_f = base_ev.cursor().execute("select fid, concept, confidence, primary_eid, meta_json, rule_id from findings f join evidence e on e.eid=f.primary_eid where replace(e.path,'\\','/')=?", (abs_in_base,)).fetchall()
                for bf in base_f:
                    be = base_ev.cursor().execute("select eid, path, start_line, end_line, snippet, sha256, parse_level, node_type from evidence where eid=?", (bf[3],)).fetchone()
                    e = {
                        "path": be[1],
                        "start_line": be[2],
                        "end_line": be[3],
                        "snippet": be[4],
                        "sha256": be[5],
                        "parse_level": be[6],
                        "node_type": be[7]
                    }
                    eid = insert_evidence(detections_db, e)
                    write_evidence_json(run_dir, eid, e)
                    r = {"concept": bf[1], "confidence": bf[2], "rule_id": bf[5], "parse_level": e["parse_level"], "path": e["path"], "start_line": e["start_line"], "end_line": e["end_line"], "snippet": e["snippet"], "meta": {}}
                    meta_json = bf[4] or "{}"
                    try:
                        m = json.loads(meta_json)
                    except:
                        m = {}
                    fid = insert_finding(detections_db, r, eid, json.dumps(m))
                    link_finding_evidence(detections_db, fid, eid)
                    report_findings.append({
                        "fid": fid,
                        "concept": r["concept"],
                        "rule_id": r.get("rule_id"),
                        "confidence": float(r["confidence"]),
                        "parse_level": r["parse_level"],
                        "path": r["path"],
                        "start_line": r["start_line"],
                        "end_line": r["end_line"],
                        "snippet": r["snippet"],
                        "primary_eid": eid
                    })
        try:
            base_ev.close()
        except:
            pass
    events = []
    report_findings = []
    for r in results:
        if len(report_findings) >= int(budget.get("max_findings", 100000)):
            warnings.append("max_findings_reached")
            break
        if r.get("parse_level") == "L1":
            insert_text_hit(idx_db, r["path"], r["rule_id"], r["start_line"], r["end_line"])
        e = {
            "path": r["path"],
            "start_line": r["start_line"],
            "end_line": r["end_line"],
            "snippet": r["snippet"],
            "sha256": sha256_file(r["path"]),
            "parse_level": r["parse_level"],
            "node_type": r.get("node_type")
        }
        eid = insert_evidence(detections_db, e)
        write_evidence_json(run_dir, eid, e)
        meta = {}
        if r.get("meta"):
            meta = r["meta"]
        meta_json = json.dumps({"rule_version": r.get("rule_version"), **meta})
        fid = insert_finding(detections_db, r, eid, meta_json)
        link_finding_evidence(detections_db, fid, eid)
        if len(events) < int(budget.get("max_events", 100000)):
            meta_obj = {}
            try:
                meta_obj = json.loads(meta_json or "{}")
            except Exception:
                meta_obj = {}
            scope = meta_obj.get("scope") or {}
            scope_key = f'{scope.get("kind","module")}:{scope.get("name","")}'
            rel = None
            try:
                rel = os.path.relpath(r["path"], repo_root).replace("\\", "/")
            except Exception:
                rel = r["path"].replace("\\", "/")
            if r.get("api_method") and r.get("api_path"):
                t = "api"
                k = f'{r["api_method"]} {r["api_path"]}'
                if (t, k) not in inserted_events:
                    lang = meta_obj.get("language")
                    fw = meta_obj.get("framework")
                    ev_meta = {
                        "path": r["path"],
                        "start_line": r["start_line"],
                        "end_line": r["end_line"],
                        "evidence_refs": [f"E{eid}"],
                        "evidence_strength": meta_obj.get("evidence_strength") or meta_obj.get("evidence_strength", "python_ast"),
                        "source_kind": meta_obj.get("evidence_strength") or "unknown",
                        "http.method": r["api_method"],
                        "http.path": r["api_path"],
                        "scope": scope,
                        "language": lang,
                        "framework": fw,
                        "parse_level": r.get("parse_level"),
                        "source": meta_obj.get("detector") or meta_obj.get("source_kind") or "unknown",
                    }
                    ev_id = insert_event(detections_db, t, k, float(r["confidence"]), json.dumps(ev_meta))
                    inserted_events.add((t, k))
                    events.append({"event_id": ev_id, "type": t, "key": k})
            pyk = meta_obj.get("python.kind")
            txk = meta_obj.get("tx.kind")
            is_ts_tx = txk in ("ts_prisma_transaction", "ts_typeorm_transaction")
            is_java_tx = txk == "java_transactional"
            if r.get("concept") == "Transaction" and (pyk == "django_atomic" or txk in ("django_atomic", "sql_begin_commit") or is_ts_tx or is_java_tx):
                t = "tx_boundary"
                kind = txk or ("django_atomic" if pyk == "django_atomic" else "unknown")
                k = f"{rel}:{scope_key}:{kind}:{r['start_line']}-{r['end_line']}"
                if (t, k) not in inserted_events:
                    src_kind = "python_ast" if pyk == "django_atomic" else ("typescript_l2" if is_ts_tx else ("java_l2" if is_java_tx else "text"))
                    ev_meta = {
                        "path": r["path"],
                        "start_line": r["start_line"],
                        "end_line": r["end_line"],
                        "evidence_refs": [f"E{eid}"],
                        "evidence_strength": meta_obj.get("evidence_strength") or meta_obj.get("evidence_strength", "python_ast"),
                        "source_kind": src_kind,
                        "tx.kind": kind,
                        "scope": scope,
                        "language": meta_obj.get("language"),
                        "framework": meta_obj.get("framework"),
                        "transaction_style": meta_obj.get("transaction_style"),
                        "callee_expr": meta_obj.get("callee_expr"),
                        "parse_level": r.get("parse_level"),
                        "source": meta_obj.get("detector") or src_kind,
                    }
                    ev_id = insert_event(detections_db, t, k, float(r["confidence"]), json.dumps(ev_meta))
                    inserted_events.add((t, k))
                    events.append({"event_id": ev_id, "type": t, "key": k})
            tsk = str(meta_obj.get("ts.kind") or "")
            jk = str(meta_obj.get("java.kind") or "")
            is_java_q = jk in ("queue_dispatch", "queue_consume")
            if r.get("concept") == "Queue" and (pyk == "celery_dispatch" or tsk in ("queue_dispatch", "queue_consume") or is_java_q):
                t = "queue_consume" if (tsk == "queue_consume" or jk == "queue_consume") else "queue_dispatch"
                qk = meta_obj.get("queue.kind") or ("ts_queue_consume" if t == "queue_consume" else "celery_dispatch")
                task = meta_obj.get("queue.task") or ""
                k = f"{rel}:{scope_key}:{qk}:{task}:{r['start_line']}"
                if (t, k) not in inserted_events:
                    src_kind = "python_ast" if pyk == "celery_dispatch" else ("java_l2" if is_java_q else "typescript_l2")
                    ev_meta = {
                        "path": r["path"],
                        "start_line": r["start_line"],
                        "end_line": r["end_line"],
                        "evidence_refs": [f"E{eid}"],
                        "evidence_strength": meta_obj.get("evidence_strength") or ("python_ast" if pyk == "celery_dispatch" else ("java_l2" if is_java_q else "typescript_l2")),
                        "source_kind": src_kind,
                        "queue.kind": qk,
                        "queue.task": task,
                        "queue_name": meta_obj.get("queue_name") or "",
                        "topic_name": meta_obj.get("topic_name") or "",
                        "queue.system": meta_obj.get("queue.system") or "",
                        "job_name": meta_obj.get("job_name") or "",
                        "consumer_style": meta_obj.get("consumer_style") or "",
                        "callee_expr": meta_obj.get("callee_expr") or "",
                        "scope": scope,
                        "language": meta_obj.get("language"),
                        "framework": meta_obj.get("framework"),
                        "parse_level": r.get("parse_level"),
                        "source": meta_obj.get("detector") or src_kind,
                    }
                    ev_id = insert_event(detections_db, t, k, float(r["confidence"]), json.dumps(ev_meta))
                    inserted_events.add((t, k))
                    events.append({"event_id": ev_id, "type": t, "key": k})
            if r.get("concept") == "DB":
                t = "db_op"
                op = str(meta_obj.get("db.op") or "")
                dstyle = str(meta_obj.get("db_style") or "")
                k = f"{rel}:{scope_key}:{dstyle}:{op}:{r['start_line']}"
                if (t, k) not in inserted_events:
                    ev_meta = {
                        "path": r["path"],
                        "start_line": r["start_line"],
                        "end_line": r["end_line"],
                        "evidence_refs": [f"E{eid}"],
                        "evidence_strength": meta_obj.get("evidence_strength") or "java_l2",
                        "source_kind": "java_l2",
                        "db.kind": meta_obj.get("db.kind") or "",
                        "db.op": op,
                        "db_style": dstyle,
                        "entity_hint": meta_obj.get("entity_hint") or "",
                        "repo_symbol": meta_obj.get("repo_symbol") or "",
                        "mapper_symbol": meta_obj.get("mapper_symbol") or "",
                        "statement_hint": meta_obj.get("statement_hint") or "",
                        "callee_expr": meta_obj.get("callee_expr") or "",
                        "scope": scope,
                        "language": meta_obj.get("language"),
                        "framework": meta_obj.get("framework"),
                        "parse_level": r.get("parse_level"),
                        "source": meta_obj.get("detector") or "java_db_ops",
                    }
                    ev_id = insert_event(detections_db, t, k, float(r["confidence"]), json.dumps(ev_meta))
                    inserted_events.add((t, k))
                    events.append({"event_id": ev_id, "type": t, "key": k})
            if r.get("concept") == "Cache" and (pyk in ("django_cache_op", "redis_op") or tsk == "cache_op"):
                t = "cache_op"
                backend = meta_obj.get("cache.backend") or ("django_cache" if pyk == "django_cache_op" else "redis")
                op = meta_obj.get("cache.op") or ""
                k = f"{rel}:{scope_key}:{backend}:{op}:{r['start_line']}"
                if (t, k) not in inserted_events:
                    src_kind = "python_ast" if pyk in ("django_cache_op", "redis_op") else "typescript_l2"
                    ev_meta = {
                        "path": r["path"],
                        "start_line": r["start_line"],
                        "end_line": r["end_line"],
                        "evidence_refs": [f"E{eid}"],
                        "evidence_strength": meta_obj.get("evidence_strength") or ("python_ast" if pyk in ("django_cache_op", "redis_op") else "typescript_l2"),
                        "source_kind": src_kind,
                        "cache.backend": backend,
                        "cache.op": op,
                        "cache.kind": meta_obj.get("cache.kind") or "",
                        "key_literal": meta_obj.get("key_literal") or "",
                        "key_expr": meta_obj.get("key_expr") or "",
                        "callee_expr": meta_obj.get("callee_expr") or "",
                        "scope": scope,
                        "language": meta_obj.get("language"),
                        "framework": meta_obj.get("framework"),
                        "parse_level": r.get("parse_level"),
                        "source": meta_obj.get("detector") or src_kind,
                    }
                    ev_id = insert_event(detections_db, t, k, float(r["confidence"]), json.dumps(ev_meta))
                    inserted_events.add((t, k))
                    events.append({"event_id": ev_id, "type": t, "key": k})
        report_findings.append({
            "fid": fid,
            "concept": r["concept"],
            "rule_id": r.get("rule_id"),
            "confidence": float(r["confidence"]),
            "parse_level": r["parse_level"],
            "path": r["path"],
            "start_line": r["start_line"],
            "end_line": r["end_line"],
            "snippet": r["snippet"],
            "primary_eid": eid
        })
    # update meta with warnings
    if base_run_dir:
        extra_meta["incremental"]["skipped_count"] = skipped
    try:
        w_str = sorted(list(set([w for w in warnings if isinstance(w, str)])))
        w_obj = [w for w in warnings if not isinstance(w, str)]
        w_all = w_str + w_obj
    except Exception:
        w_all = warnings
    stats = {"walk": walk_stats, "warnings": w_all}
    if content_id:
        stats["content_id"] = content_id
    if pack_id:
        stats["pack_id"] = pack_id
    write_meta(run_dir, {"version": "0.1.0"}, ruleset["version"], {"budget": budget, "budget_path": budget_path, "ruleset_dir": ruleset_dir, "warnings": stats["warnings"], "stats": stats, **({"incremental": extra_meta.get("incremental")} if base_run_dir else {})})
    stats["schema_version"] = 1
    stats["generated_by"] = generated_by("0.1.0", os.path.basename(ruleset_dir), rs_fp, 1)
    write_coverage(run_dir, stats)
    build_graph(run_dir)
    # build run_summary by reading artifacts
    run_summary = {}
    try:
        with open(os.path.join(run_dir, "coverage.json"), "r", encoding="utf-8") as f:
            cov = json.load(f)
    except Exception:
        cov = {}
    try:
        with open(os.path.join(run_dir, "event_graph.json"), "r", encoding="utf-8") as f:
            g = json.load(f)
    except Exception:
        g = {"nodes": [], "edges": []}
    findings_count = len(report_findings)
    events_count = 0
    try:
        import sqlite3
        con = sqlite3.connect(os.path.join(run_dir, "detections.sqlite"))
        cur = con.cursor()
        events_count = int(cur.execute("select count(1) from events").fetchone()[0])
        # evidence strength breakdown from findings meta_json
        rows = cur.execute("select meta_json from findings").fetchall()
        es_counts = {}
        for (mj,) in rows:
            try:
                m = json.loads(mj or "{}")
            except Exception:
                m = {}
            es = m.get("evidence_strength") or ""
            if es:
                es_counts[es] = es_counts.get(es, 0) + 1
        con.close()
    except Exception:
        es_counts = {}
    walk = (cov.get("walk") or {})
    skipped = walk.get("skipped") or {}
    top_skip = sorted(skipped.items(), key=lambda x: x[1], reverse=True)[:5]
    truncation = {
        "budget_cut": bool(walk.get("budget_cut_reached")),
        "findings_truncated": any(x == "max_findings_reached" for x in (cov.get("warnings") or cov.get("warnings") or [])),
        "events_truncated": events_count >= int(budget.get("max_events", 100000)),
    }
    demo_mode = (os.path.basename(budget_path).lower() in ("demo.json",)) or ("demo_v1" in (ruleset_dir.replace("\\","/").lower()))
    detected_langs, detected_frameworks = collect_detected_languages_frameworks(report_findings, g.get("nodes") or [])
    run_summary = {
        "profile": os.path.basename(budget_path).replace("\\", "/"),
        "ruleset": ruleset_dir.replace("\\", "/"),
        "budget": budget,
        "scanned_files": int(walk.get("included_files") or 0),
        "total_bytes": int(walk.get("included_bytes") or 0),
        "skipped_files_by_reason": top_skip,
        "findings_count": findings_count,
        "events_count": events_count,
        "graph_nodes": len(g.get("nodes") or []),
        "graph_edges": len(g.get("edges") or []),
        "graph_edges_by_type": (lambda es: {t: es.count(t) for t in sorted(set(es))})([e.get("type") for e in (g.get("edges") or [])]),
        "truncation": truncation,
        "warnings_count": len(cov.get("warnings") or []),
        "warnings_top": (cov.get("warnings") or [])[:5],
        "evidence_strength_breakdown": es_counts,
        "artifacts_missing": [],
        "demo_mode": bool(demo_mode),
        "registered_languages": list_registered_languages(),
        "detected_languages": detected_langs,
        "detected_frameworks": detected_frameworks,
    }
    if not cov:
        run_summary["artifacts_missing"].append("coverage.json")
    if not g.get("nodes"):
        run_summary["artifacts_missing"].append("event_graph.json")
    report = {
        "schema_version": 1,
        "engine_version": "0.1.0",
        "ruleset_version": ruleset["version"]["version"],
        "budget_profile": "meta/config.json",
        "findings": report_findings,
        "run_summary": run_summary,
        "generated_by": generated_by("0.1.0", os.path.basename(ruleset_dir), rs_fp, 1)
    }
    write_report_json(run_dir, report)
    try:
        build_api_surface(run_dir)
    except Exception:
        pass
    try:
        build_cross_language_exports(run_dir)
    except Exception:
        pass
    try:
        build_entrypoints(manifest.get("repo_root"), run_dir)
    except Exception:
        pass
    try:
        build_language_capabilities(run_dir)
    except Exception:
        pass
    try:
        export_patterns(run_dir)
    except Exception:
        pass
    try:
        build_context_pack(run_dir, top_n=10)
        zip_context_pack(run_dir)
    except Exception:
        pass
    try:
        idx_db.close()
    except:
        pass
    try:
        detections_db.close()
    except:
        pass
    build_report_html(run_dir)
    print(run_dir)
    return run_dir

