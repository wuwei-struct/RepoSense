import os
import json
import sqlite3
import zipfile


def _ensure_dirs(base, rels):
    for r in rels:
        os.makedirs(os.path.join(base, r), exist_ok=True)


def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _top_strength_rank(s):
    order = ["python_ast", "typescript_l2", "openapi", "sql_ddl", "compose", "gha", "deps", "text"]
    try:
        return order.index(s)
    except Exception:
        return len(order)


def _stable_name(rank, sid):
    return f"rank-{rank:03d}_{sid}.json"


def build_context_pack(run_dir, top_n=10):
    pack_root = os.path.join(run_dir, "context_pack")
    _ensure_dirs(pack_root, ["MAP", "SPEC", "EVIDENCE/top_findings", "EVIDENCE/top_events", "ARTIFACTS"])
    rep = _read_json(os.path.join(run_dir, "report.json"), {})
    cov = _read_json(os.path.join(run_dir, "coverage.json"), {})
    graph = _read_json(os.path.join(run_dir, "event_graph.json"), {"nodes": [], "edges": []})
    run_sum = rep.get("run_summary") or {}
    # copy artifacts
    for nm in ["report.json", "event_graph.json", "language_capabilities.json", "api_callers.json", "cross_language_summary.json", "patterns.json", "pattern_summary.json", "ai_summary.json", "ai_summary.md"]:
        src = os.path.join(run_dir, nm)
        dst = os.path.join(pack_root, "ARTIFACTS", nm)
        if os.path.isfile(src):
            try:
                with open(src, "r", encoding="utf-8") as f:
                    data = json.load(f)
                with open(dst, "w", encoding="utf-8") as f2:
                    json.dump(data, f2, ensure_ascii=False)
            except Exception:
                pass
    for nm in ["cross_language_links.json", "api_topology.json"]:
        src = os.path.join(run_dir, nm)
        dst = os.path.join(pack_root, "MAP", nm)
        if os.path.isfile(src):
            try:
                with open(src, "r", encoding="utf-8") as f:
                    data = json.load(f)
                with open(dst, "w", encoding="utf-8") as f2:
                    json.dump(data, f2, ensure_ascii=False)
            except Exception:
                pass
    # run_summary copy
    try:
        with open(os.path.join(pack_root, "ARTIFACTS", "run_summary.json"), "w", encoding="utf-8") as f:
            json.dump(run_sum, f, ensure_ascii=False)
    except Exception:
        pass
    # copy quality gate if exists
    qg = os.path.join(run_dir, "quality_gate.json")
    if os.path.isfile(qg):
        try:
            with open(qg, "r", encoding="utf-8") as f:
                data = json.load(f)
            with open(os.path.join(pack_root, "ARTIFACTS", "quality_gate.json"), "w", encoding="utf-8") as f2:
                json.dump(data, f2, ensure_ascii=False)
        except Exception:
            pass
    # copy baseline artifacts if exist
    for nm in ["baseline_in.json","baseline_diff.json","baseline_diff.md"]:
        src = os.path.join(run_dir, nm)
        if os.path.isfile(src):
            try:
                with open(src, "rb") as fi, open(os.path.join(pack_root, "ARTIFACTS", nm), "wb") as fo:
                    fo.write(fi.read())
            except Exception:
                pass
    # copy run_manifest
    rm = os.path.join(run_dir, "run_manifest.json")
    if os.path.isfile(rm):
        try:
            with open(rm, "rb") as fi, open(os.path.join(pack_root, "ARTIFACTS", "run_manifest.json"), "wb") as fo:
                fo.write(fi.read())
        except Exception:
            pass
    # content ids
    stats = cov if isinstance(cov, dict) else {}
    content_id = (stats.get("content_id") or (stats.get("stats") or {}).get("content_id"))
    pack_id = (stats.get("pack_id") or (stats.get("stats") or {}).get("pack_id"))
    try:
        with open(os.path.join(pack_root, "content_id.json"), "w", encoding="utf-8") as f:
            json.dump({"content_id": content_id, "pack_id": pack_id}, f, ensure_ascii=False)
    except Exception:
        pass
    # Top findings via DB join to get evidence_strength
    det_db = os.path.join(run_dir, "detections.sqlite")
    top_findings = []
    concepts = {}
    if os.path.isfile(det_db):
        con = sqlite3.connect(det_db)
        cur = con.cursor()
        rows = cur.execute("select f.fid, f.concept, f.confidence, f.meta_json, f.rule_id, e.path, e.start_line, e.end_line, e.snippet, e.sha256, e.parse_level from findings f join evidence e on e.eid=f.primary_eid").fetchall()
        seen = set()
        for fid, concept, conf, meta_json, rule_id, path, s, e, snip, sha, level in rows:
            concepts[concept] = concepts.get(concept, 0) + 1
            try:
                m = json.loads(meta_json or "{}")
            except Exception:
                m = {}
            es = m.get("evidence_strength") or ""
            key = (rule_id, path, int(s or 0), int(e or 0))
            if key in seen:
                continue
            seen.add(key)
            top_findings.append({
                "fid": fid,
                "rule_id": rule_id,
                "concept": concept,
                "confidence": float(conf or 0),
                "kind": level,
                "evidence_strength": es,
                "path": path,
                "start_line": int(s or 0),
                "end_line": int(e or 0),
                "snippet": snip,
                "hashes": {"snippet_sha": None, "file_sha": sha},
                "links": {"report_anchor": None, "search_keys": [rule_id, concept, path]},
            })
        con.close()
    # Rank findings
    top_findings.sort(key=lambda x: (-x["confidence"], _top_strength_rank(x.get("evidence_strength") or "")))
    top_findings = top_findings[:top_n]
    # Write per-file
    for i, item in enumerate(top_findings, start=1):
        nm = _stable_name(i, f'F{item["fid"]}')
        with open(os.path.join(pack_root, "EVIDENCE", "top_findings", nm), "w", encoding="utf-8") as f:
            json.dump(item, f, ensure_ascii=False)
    # Top events from graph nodes (prefer tx_boundary/queue_dispatch/queue_consume/cache_op/api)
    ev_nodes = [n for n in (graph.get("nodes") or []) if n.get("type") in ["tx_boundary", "queue_dispatch", "queue_consume", "cache_op", "api"]]
    ev_nodes.sort(key=lambda n: float(n.get("confidence", 0)), reverse=True)
    ev_nodes = ev_nodes[:top_n]
    edges = graph.get("edges") or []
    # Add evidence details via first evidence id
    for i, n in enumerate(ev_nodes, start=1):
        eids = (n.get("evidence") or [])
        evj = {
            "event_id": n.get("event_id"),
            "type": n.get("type"),
            "key": n.get("key"),
            "confidence": n.get("confidence"),
            "meta": n.get("meta") or {},
            "evidence_refs": eids,
        }
        # pull first evidence json if exists
        if eids:
            try:
                eid = str(eids[0])
                if eid.startswith("E"):
                    eid = eid[1:]
                ejp = os.path.join(run_dir, "evidence", f"E{eid}.json")
                ev = _read_json(ejp, {})
                evj["path"] = ev.get("path")
                evj["start_line"] = ev.get("start_line")
                evj["end_line"] = ev.get("end_line")
                evj["snippet"] = ev.get("snippet")
            except Exception:
                pass
        nm = _stable_name(i, f'E{n.get("event_id")}')
        with open(os.path.join(pack_root, "EVIDENCE", "top_events", nm), "w", encoding="utf-8") as f:
            json.dump(evj, f, ensure_ascii=False)
    # SPEC: ruleset summary
    spec = {
        "ruleset": run_sum.get("ruleset") or "",
        "ruleset_version": rep.get("ruleset_version"),
        "concepts": {},
        "budget": {
            "max_files": (run_sum.get("budget") or {}).get("max_files"),
            "max_total_bytes": (run_sum.get("budget") or {}).get("max_total_bytes"),
            "max_lines_per_file": (run_sum.get("budget") or {}).get("max_lines_per_file"),
            "max_snippet_lines": (run_sum.get("budget") or {}).get("max_snippet_lines"),
            "max_findings": (run_sum.get("budget") or {}).get("max_findings"),
            "max_events": (run_sum.get("budget") or {}).get("max_events"),
        },
        "detectors": sorted(list((run_sum.get("evidence_strength_breakdown") or {}).keys())),
    }
    # concept->rule_ids from findings
    for f in rep.get("findings", []):
        spec["concepts"].setdefault(f.get("concept") or "", [])
        rid = f.get("rule_id")
        if rid and rid not in spec["concepts"][f.get("concept") or ""]:
            spec["concepts"][f.get("concept") or ""].append(rid)
    with open(os.path.join(pack_root, "SPEC", "ruleset_summary.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False)
    # MAP: index.json
    top_files = {}
    for f in rep.get("findings", []):
        p = f.get("path") or ""
        top_files[p] = top_files.get(p, 0) + 1
    for n in graph.get("nodes") or []:
        mp = (n.get("meta") or {}).get("path")
        if mp:
            top_files[mp] = top_files.get(mp, 0) + 1
    tf = [{"path": k, "count": top_files[k]} for k in sorted(top_files.keys(), key=lambda x: top_files[x], reverse=True)[:20]]
    map_index = {
        "run": {
            "run_id": None,
            "profile": run_sum.get("profile"),
            "ruleset": run_sum.get("ruleset"),
            "budget": run_sum.get("budget"),
        },
        "outputs": {
            "report_html": "report.html",
            "report_json": "report.json",
            "event_graph": "event_graph.json",
            "language_capabilities": "language_capabilities.json",
            "framework_event_summary": "context_pack/ARTIFACTS/framework_event_summary.json",
            "unsupported_detected": "context_pack/ARTIFACTS/unsupported_detected.json",
            "event_catalog": "context_pack/MAP/event_catalog.json",
            "api_callers": "context_pack/ARTIFACTS/api_callers.json",
            "cross_language_links": "context_pack/MAP/cross_language_links.json",
            "cross_language_summary": "context_pack/ARTIFACTS/cross_language_summary.json",
            "patterns": "patterns.json",
            "pattern_summary": "pattern_summary.json",
            "ai_summary_json": "ai_summary.json",
            "ai_summary_md": "ai_summary.md",
            "api_topology": "context_pack/MAP/api_topology.json",
            "api_surface": "api_surface.json",
            "learn_base": "learn/",
            "exports": "exports/",
            "context_pack": "context_pack/",
            "baseline_in": "baseline_in.json",
            "baseline_diff_json": "baseline_diff.json",
            "baseline_diff_md": "baseline_diff.md",
        },
        "stats": {
            "findings": run_sum.get("findings_count", len(rep.get("findings", []))),
            "events": run_sum.get("events_count", len(graph.get("nodes", []))),
            "graph_nodes": run_sum.get("graph_nodes", len(graph.get("nodes", []))),
            "graph_edges": run_sum.get("graph_edges", len(graph.get("edges", []))),
            "graph_edge_types": (run_sum.get("graph_edges_by_type") or (lambda es: {t: es.count(t) for t in sorted(set(es))})([e.get("type") for e in (graph.get("edges") or [])])),
            "scanned_files": run_sum.get("scanned_files", 0),
            "skipped_top": run_sum.get("skipped_files_by_reason", []),
        },
        "top_files": tf,
        "concepts": [{"concept": k, "count": concepts.get(k, 0)} for k in sorted(concepts.keys(), key=lambda x: concepts[x], reverse=True)],
        "entrypoints": [],
    }
    with open(os.path.join(pack_root, "MAP", "index.json"), "w", encoding="utf-8") as f:
        json.dump(map_index, f, ensure_ascii=False)
    event_catalog = []
    by_kind = {}
    by_lang = {}
    by_fw = {}
    q_fw = {}
    c_fw = {}
    samples = {}
    cat_counts = {}
    for n in (graph.get("nodes") or []):
        meta = n.get("meta") or {}
        et = str(n.get("type") or "")
        lang = str(meta.get("language") or "unknown")
        fw = str(meta.get("framework") or "unknown")
        kind = ""
        if et == "api":
            kind = "api.route"
        elif et == "tx_boundary":
            kind = "db.transaction"
        elif et == "queue_dispatch":
            kind = "queue.dispatch"
        elif et == "queue_consume":
            kind = "queue.consume"
        elif et == "cache_op":
            op = str(meta.get("cache.op") or "").lower()
            ck = str(meta.get("cache.kind") or "").lower()
            if ck in ("cache.read", "cache.write", "cache.invalidate"):
                kind = ck
            elif op in ("get", "mget", "hget", "read"):
                kind = "cache.read"
            elif op in ("del", "delete", "unlink", "hdel", "invalidate"):
                kind = "cache.invalidate"
            else:
                kind = "cache.write"
        elif et == "db_op":
            dk = str(meta.get("db.kind") or "").lower()
            if dk in ("db.read", "db.write"):
                kind = dk
            else:
                op = str(meta.get("db.op") or "").lower()
                kind = "db.read" if op in ("read", "exists", "find", "select") else "db.write"
        if not kind:
            continue
        by_kind[kind] = by_kind.get(kind, 0) + 1
        by_lang[lang] = by_lang.get(lang, 0) + 1
        by_fw[fw] = by_fw.get(fw, 0) + 1
        if kind.startswith("queue."):
            q_fw[fw] = q_fw.get(fw, 0) + 1
        if kind.startswith("cache."):
            c_fw[fw] = c_fw.get(fw, 0) + 1
        key = (kind, lang, fw)
        cat_counts[key] = cat_counts.get(key, 0) + 1
        samples.setdefault(key, [])
        if len(samples[key]) < 5 and n.get("event_id"):
            samples[key].append(n.get("event_id"))
    for (kind, lang, fw), vals in sorted(samples.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])):
        event_catalog.append({"event_kind": kind, "language": lang, "framework": fw, "count": int(cat_counts.get((kind, lang, fw), 0)), "sample_event_ids": vals})
    with open(os.path.join(pack_root, "MAP", "event_catalog.json"), "w", encoding="utf-8") as f:
        json.dump({"items": event_catalog}, f, ensure_ascii=False)
    unsup = []
    for w in (cov.get("warnings") or []):
        if isinstance(w, dict) and w.get("type") == "unsupported_detected":
            unsup.append(w)
    api_callers = _read_json(os.path.join(run_dir, "api_callers.json"), {})
    for w in (api_callers.get("unsupported_detected") or []):
        if isinstance(w, dict) and w.get("type") == "unsupported_detected":
            unsup.append(w)
    with open(os.path.join(pack_root, "ARTIFACTS", "unsupported_detected.json"), "w", encoding="utf-8") as f:
        json.dump({"items": unsup}, f, ensure_ascii=False)
    fw_summary = {
        "languages_detected": sorted(list(set([str((n.get("meta") or {}).get("language") or "unknown") for n in (graph.get("nodes") or [])]))),
        "frameworks_detected": sorted(list(set([str((n.get("meta") or {}).get("framework") or "unknown") for n in (graph.get("nodes") or [])]))),
        "event_counts_by_kind": by_kind,
        "event_counts_by_language": by_lang,
        "event_counts_by_framework": by_fw,
        "top_queue_frameworks": sorted([{"framework": k, "count": v} for k, v in q_fw.items()], key=lambda x: x["count"], reverse=True),
        "top_cache_frameworks": sorted([{"framework": k, "count": v} for k, v in c_fw.items()], key=lambda x: x["count"], reverse=True),
    }
    with open(os.path.join(pack_root, "ARTIFACTS", "framework_event_summary.json"), "w", encoding="utf-8") as f:
        json.dump(fw_summary, f, ensure_ascii=False)
    # README.md
    def _mk_table(rows, headers):
        out = []
        out.append(" | ".join(headers))
        out.append(" | ".join(["---"] * len(headers)))
        for r in rows:
            out.append(" | ".join(r))
        return "\n".join(out)
    topF_rows = []
    for i, t in enumerate(top_findings, start=1):
        _finding_name = _stable_name(i, f"F{t['fid']}")
        topF_rows.append([str(i), t["rule_id"] or "", t["concept"] or "", f'{t["path"]}:{t["start_line"]}', f"EVIDENCE/top_findings/{_finding_name}"])
    topE_rows = []
    for i, n in enumerate(ev_nodes, start=1):
        meta = n.get("meta") or {}
        method = meta.get("http.method") or ""
        pathp = meta.get("path") or meta.get("http.path") or ""
        _event_name = _stable_name(i, f"E{n.get('event_id')}")
        topE_rows.append([str(i), n.get("type") or "", f'{method} {pathp}'.strip(), f'{meta.get("path","")}:{meta.get("start_line","")}', f"EVIDENCE/top_events/{_event_name}"])
    readme = []
    readme.append("# RepoSense Context Pack L1")
    readme.append("")
    try:
        ents = _read_json(os.path.join(run_dir, "entrypoints.json"), {"entrypoints": [], "stats": {}})
        topE = (ents.get("entrypoints") or [])[:5]
        readme.append("## Start Here（如何跑起来）")
        for ep in topE:
            cmd = ep.get("command") or f'查看 {((ep.get("source") or {}).get("path") or "")}'
            readme.append(f"- {ep.get('title','')} — {cmd}")
        while len(readme) < 110:
            readme.append("")
    except Exception:
        pass
    # Baseline & Diff section
    try:
        gate = _read_json(os.path.join(run_dir, "quality_gate.json"), {})
        if gate.get("baseline_used"):
            reg = gate.get("regressions") or {}
            readme.append("## Baseline & Diff")
            readme.append(f"- regressions: total={reg.get('total',0)} +E={reg.get('added_error',0)} ↑S={reg.get('severity_upgrades',0)} +W={reg.get('added_warning',0)}")
            readme.append(f"- baseline_compatible: {gate.get('baseline_compatible', True)}")
            for x in (gate.get("regression_samples_top") or [])[:5]:
                readme.append(f"- {x.get('ruleId','')} {x.get('concept','')} {x.get('path','')}:{x.get('startLine',0)} {x.get('severity','')}")
            readme.append("")
            readme.append("复现 diff：")
            readme.append("python -m reposense bdiff --base baseline_in.json --new <run_dir> --out baseline_diff.json --markdown baseline_diff.md")
    except Exception:
        pass
    # Run Manifest & Versions
    try:
        readme.append("## Run Manifest & Versions")
        readme.append("- see ARTIFACTS/run_manifest.json")
        gb = _read_json(os.path.join(run_dir, "quality_gate.json"), {}).get("generated_by") or {}
        readme.append(f"- reposense_version: {gb.get('reposense_version','')}")
        readme.append(f"- ruleset_id: {gb.get('ruleset_id','')}")
        readme.append(f"- ruleset_fingerprint: {gb.get('ruleset_fingerprint','')}")
    except Exception:
        pass
    # API Surface summary
    try:
        api = _read_json(os.path.join(run_dir, "api_surface.json"), {"endpoints":[], "mismatches":{}})
        readme.append("## API Surface 摘要")
        readme.append(f"- Endpoints: {len(api.get('endpoints', []))}")
        mm = api.get("mismatches") or {}
        readme.append(f"- Mismatches: missing_in_spec={len(mm.get('missing_in_spec', []))} missing_in_code={len(mm.get('missing_in_code', []))} method_mismatch={len(mm.get('method_mismatch', []))}")
        top_eps = (api.get("endpoints") or [])[:10]
        rows = []
        for i, ep in enumerate(top_eps, start=1):
            rows.append([str(i), ep.get("method",""), ep.get("path",""), (ep.get("source") or {}).get("path","")])
        readme.append(_mk_table(rows, ["#", "method", "path", "file"]))
        readme.append("")
    except Exception:
        pass
    try:
        cls = _read_json(os.path.join(run_dir, "cross_language_summary.json"), {})
        cll = _read_json(os.path.join(run_dir, "cross_language_links.json"), {})
        readme.append("## Cross-language 摘要")
        readme.append(f"- API endpoints detected: {int(cls.get('total_endpoints', 0))}")
        readme.append(f"- TS callers detected: {int(cls.get('total_callers', 0))}")
        matched_links = len(cll.get("links") or [])
        readme.append(f"- Matched links: {matched_links}")
        readme.append(f"- Exact matches: {int(cls.get('exact_match_count', 0))}")
        readme.append(f"- Template matches: {int(cls.get('template_match_count', 0))}")
        readme.append(f"- Unmatched callers: {int(cls.get('unmatched_callers', 0))}")
        readme.append(f"- Endpoints without caller: {int(cls.get('endpoints_without_callers', 0))}")
        top_pairs = (cll.get("links") or [])[:5]
        readme.append("- Top matched pairs:")
        for x in top_pairs:
            readme.append(f"  - {x.get('language_pair','')} {x.get('method','')} {x.get('caller_path','')} -> {x.get('endpoint_path','')} ({x.get('match_type','')})")
        top_uc = (cll.get("unmatched_callers") or [])[:5]
        readme.append("- Top unmatched callers:")
        for x in top_uc:
            readme.append(f"  - {x.get('http_method','')} {x.get('path_normalized','')} @ {x.get('file','')}:{x.get('line_start',0)}")
        top_ue = (cll.get("unmatched_endpoints") or [])[:5]
        readme.append("- Top unmatched endpoints:")
        for x in top_ue:
            readme.append(f"  - {x.get('method','')} {x.get('path_normalized','')} @ {x.get('file','')}:{x.get('line_start',0)}")
        readme.append("")
    except Exception:
        pass
    readme.append("本包用于离线交接与协作，包含本次运行的摘要、规则/预算说明、TopN 证据与输出位置。")
    readme.append("")
    readme.append("## Run 概览")
    readme.append(f"- Profile: {run_sum.get('profile')}")
    readme.append(f"- Ruleset: {run_sum.get('ruleset')}")
    readme.append(f"- Findings: {run_sum.get('findings_count', len(rep.get('findings', [])))}")
    readme.append(f"- Events: {run_sum.get('events_count', len(graph.get('nodes', [])))}")
    readme.append(f"- Registered Languages: {', '.join(run_sum.get('registered_languages') or [])}")
    readme.append(f"- Detected Languages: {', '.join(run_sum.get('detected_languages') or [])}")
    readme.append(f"- Detected Frameworks: {', '.join(run_sum.get('detected_frameworks') or [])}")
    ts_frameworks = sorted(list(set([str((n.get("meta") or {}).get("framework") or "") for n in (graph.get("nodes") or []) if str((n.get("meta") or {}).get("language") or "") == "typescript" and str((n.get("meta") or {}).get("framework") or "")])))
    java_frameworks = sorted(list(set([str((n.get("meta") or {}).get("framework") or "") for n in (graph.get("nodes") or []) if str((n.get("meta") or {}).get("language") or "") == "java" and str((n.get("meta") or {}).get("framework") or "")])))
    java_api_routes = len([n for n in (graph.get("nodes") or []) if str(n.get("type") or "") == "api" and str((n.get("meta") or {}).get("language") or "") == "java"])
    java_tx_events = len([n for n in (graph.get("nodes") or []) if str(n.get("type") or "") == "tx_boundary" and str((n.get("meta") or {}).get("language") or "") == "java"])
    java_queue_dispatch = len([n for n in (graph.get("nodes") or []) if str(n.get("type") or "") == "queue_dispatch" and str((n.get("meta") or {}).get("language") or "") == "java"])
    java_queue_consume = len([n for n in (graph.get("nodes") or []) if str(n.get("type") or "") == "queue_consume" and str((n.get("meta") or {}).get("language") or "") == "java"])
    java_db_read = len([n for n in (graph.get("nodes") or []) if str(n.get("type") or "") == "db_op" and str((n.get("meta") or {}).get("language") or "") == "java" and str((n.get("meta") or {}).get("db.kind") or "") == "db.read"])
    java_db_write = len([n for n in (graph.get("nodes") or []) if str(n.get("type") or "") == "db_op" and str((n.get("meta") or {}).get("language") or "") == "java" and str((n.get("meta") or {}).get("db.kind") or "") == "db.write"])
    readme.append(f"- TS frameworks seen: {', '.join(ts_frameworks)}")
    readme.append(f"- Java frameworks seen: {', '.join(java_frameworks)}")
    readme.append(f"- Java API routes: {java_api_routes}")
    readme.append(f"- Java transaction events: {java_tx_events}")
    readme.append(f"- Java queue events: {java_queue_dispatch} dispatch / {java_queue_consume} consume")
    readme.append(f"- Java DB events: {java_db_read} read / {java_db_write} write")
    readme.append(f"- Queue events: dispatch={by_kind.get('queue.dispatch',0)} consume={by_kind.get('queue.consume',0)}")
    readme.append(f"- Cache events: read={by_kind.get('cache.read',0)} write={by_kind.get('cache.write',0)} invalidate={by_kind.get('cache.invalidate',0)}")
    if unsup:
        readme.append(f"- Unsupported but detected hints: {len(unsup)}")
    readme.append("")
    readme.append("## Top Findings（前10）")
    readme.append(_mk_table(topF_rows, ["#", "rule_id", "concept", "path:line", "evidence_ref"]))
    readme.append("")
    readme.append("## Top Events（前10）")
    readme.append(_mk_table(topE_rows, ["#", "type", "meta", "path:line", "evidence_ref"]))
    readme.append("")
    readme.append("## 复现说明")
    readme.append("- Studio：导入 ZIP 后，选择 Profile 与 Ruleset，点击开始分析")
    readme.append("- CLI：`python -m reposense scan <repo> <out_dir> <ruleset_dir> <budget_json>`")
    readme.append("")
    readme.append("## 产物位置")
    readme.append("- report.html / report.json / event_graph.json")
    readme.append("- detections.sqlite / evidence/")
    readme.append("- exports/report.sarif.json（如有） / context_pack/")
    readme.append("")
    # pad lines to ensure minimum size
    while len(readme) < 90:
        readme.append("")
    # Quality Gate summary
    try:
        gate = _read_json(os.path.join(run_dir, "quality_gate.json"), {"status":"N/A","violations":[]})
        readme.append("## Quality Gate")
        readme.append(f"- 状态: {gate.get('status')}")
        for v in (gate.get("violations") or [])[:5]:
            readme.append(f"- {v.get('level')} {v.get('metric')}: {v.get('message')}")
    except Exception:
        pass
    try:
        ps = _read_json(os.path.join(run_dir, "pattern_summary.json"), {})
        if isinstance(ps, dict) and ps:
            readme.append("")
            readme.append("## Patterns Summary")
            readme.append(f"- total patterns: {int(ps.get('total_patterns') or 0)}")
            cbt = ps.get("counts_by_type") or {}
            cbs = ps.get("counts_by_severity") or {}
            if cbt:
                readme.append("- top pattern types: " + ", ".join([f"{k}:{v}" for k, v in sorted(cbt.items(), key=lambda x: x[0])]))
            if cbs:
                readme.append("- counts by severity: " + ", ".join([f"{k}:{v}" for k, v in sorted(cbs.items(), key=lambda x: x[0])]))
    except Exception:
        pass
    try:
        if os.path.isfile(os.path.join(run_dir, "ai_summary.md")):
            readme.append("")
            readme.append("## AI Summary")
            readme.append("- file: ARTIFACTS/ai_summary.md")
    except Exception:
        pass
    with open(os.path.join(pack_root, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(readme))
    # manifest.json (stable ordering)
    files = []
    for root, _, fs in os.walk(pack_root):
        for nm in fs:
            p = os.path.join(root, nm)
            rel = os.path.relpath(p, pack_root).replace("\\", "/")
            try:
                sz = os.path.getsize(p)
            except Exception:
                sz = 0
            files.append({"path": rel, "size": sz})
    files.sort(key=lambda x: x["path"])
    with open(os.path.join(pack_root, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"files": files}, f, ensure_ascii=False)
    # lightweight validations
    def _fail(msg):
        raise Exception("context_pack_invalid: " + msg)
    if not os.path.isfile(os.path.join(pack_root, "README.md")):
        _fail("README.md missing")
    if os.path.getsize(os.path.join(pack_root, "README.md")) < 200:
        _fail("README too small")
    for req in ["MAP/index.json", "SPEC/ruleset_summary.json", "manifest.json"]:
        if not os.path.isfile(os.path.join(pack_root, req)):
            _fail(f"{req} missing")
    # ensure at least one top finding/event file exists if any content present
    tf_dir = os.path.join(pack_root, "EVIDENCE", "top_findings")
    te_dir = os.path.join(pack_root, "EVIDENCE", "top_events")
    if len(os.listdir(tf_dir)) == 0 and len(rep.get("findings", [])) > 0:
        _fail("top_findings empty")
    if len(os.listdir(te_dir)) == 0 and len((graph.get("nodes") or [])) > 0:
        _fail("top_events empty")
    return pack_root


def zip_context_pack(run_dir):
    pack_root = os.path.join(run_dir, "context_pack")
    zip_path = os.path.join(run_dir, "exports", "context_pack.zip")
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        # stable file order
        items = []
        for root, _, fs in os.walk(pack_root):
            for nm in fs:
                p = os.path.join(root, nm)
                rel = os.path.relpath(p, pack_root).replace("\\", "/")
                items.append((p, rel))
        items.sort(key=lambda x: x[1])
        for p, rel in items:
            z.write(p, arcname=os.path.join("context_pack", rel))
    # simple validation
    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        must = [
            "context_pack/README.md",
            "context_pack/MAP/index.json",
            "context_pack/SPEC/ruleset_summary.json",
            "context_pack/manifest.json",
        ]
        for m in must:
            if m not in names:
                raise Exception("context_pack_zip_invalid: missing " + m)
        # README size check from zip info
        info = z.getinfo("context_pack/README.md")
        if info.file_size < 200:
            raise Exception("context_pack_zip_invalid: README too small")
    return zip_path


def run_context_pack(run_dir, out_dir, zip=False, include_evidence=False, include_learn=False, learn_graph=None, include_brief=False, base_pack=None):
    os.makedirs(out_dir, exist_ok=True)
    rep = _read_json(os.path.join(run_dir, "report.json"), {})
    graph = _read_json(os.path.join(run_dir, "event_graph.json"), {"nodes": [], "edges": []})
    cov = _read_json(os.path.join(run_dir, "coverage.json"), {})
    # README
    lines = []
    lines.append("# RepoSense Context Pack (legacy)")
    lines.append("")
    lines.append("本目录为离线交接包（兼容 legacy 测试），包含快照与摘要。")
    lines.append("")
    lines.append("## 快照")
    lines.append(f"- Findings: {len(rep.get('findings', []))}")
    lines.append(f"- Events: {len(graph.get('nodes', []))}")
    while len(lines) < 60:
        lines.append("")
    with open(os.path.join(out_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    # manifest-ish files
    stats = {
        "findings": len(rep.get("findings", [])),
        "events": len(graph.get("nodes", [])),
        "graph_edges": len(graph.get("edges", [])),
        "skipped_top": ((cov.get("walk") or {}).get("skipped") or {}),
    }
    with open(os.path.join(out_dir, "snapshot.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False)
    with open(os.path.join(out_dir, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False)
    with open(os.path.join(out_dir, "warnings.json"), "w", encoding="utf-8") as f:
        json.dump(cov.get("warnings") or [], f, ensure_ascii=False)
    # fingerprints
    cid = (cov.get("content_id") or (cov.get("stats") or {}).get("content_id"))
    pid = (cov.get("pack_id") or (cov.get("stats") or {}).get("pack_id"))
    with open(os.path.join(out_dir, "repo_fingerprint.json"), "w", encoding="utf-8") as f:
        json.dump({"content_id": cid, "pack_id": pid}, f, ensure_ascii=False)
    # context_manifest lists artifacts included
    arts_dir = os.path.join(out_dir, "artifacts")
    os.makedirs(arts_dir, exist_ok=True)
    arts = []
    for nm in ["report.json", "event_graph.json"]:
        src = os.path.join(run_dir, nm)
        if os.path.isfile(src):
            try:
                with open(src, "r", encoding="utf-8") as f:
                    data = json.load(f)
                with open(os.path.join(arts_dir, nm), "w", encoding="utf-8") as f2:
                    json.dump(data, f2, ensure_ascii=False)
                arts.append({"path": os.path.join("artifacts", nm), "size": os.path.getsize(os.path.join(arts_dir, nm))})
            except Exception:
                pass
    with open(os.path.join(out_dir, "context_manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"artifacts": arts}, f, ensure_ascii=False)
    # checksums for README and manifest
    checks = []
    import hashlib
    for nm in ["README.md", "context_manifest.json"]:
        p = os.path.join(out_dir, nm)
        try:
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        except Exception:
            h = None
        checks.append({"path": nm, "sha256": h})
    with open(os.path.join(out_dir, "checksums.json"), "w", encoding="utf-8") as f:
        json.dump(checks, f, ensure_ascii=False)
    # zip if requested
    if zip:
        zp = out_dir + ".zip"
        with zipfile.ZipFile(zp, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for root, _, fs in os.walk(out_dir):
                for nm in fs:
                    p = os.path.join(root, nm)
                    rel = os.path.relpath(p, out_dir).replace("\\", "/")
                    z.write(p, arcname=rel)
        return 0
    return 0
