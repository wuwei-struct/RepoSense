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


REVIEW_ARTIFACTS = [
    ("repository_review_report.md", "Repository-level evidence-guided review report."),
    ("review_risk_matrix.json", "Repository review decision and risk matrix."),
    ("human_review_required.md", "Human review queue for risky paths and artifacts."),
    ("backend_verifier_report.md", "Backend transaction, side-effect, and evidence summary."),
    ("code_health_summary.json", "Code Health Radar counts, top files, and experimental score."),
    ("maintainability_risks.json", "Code Health risks normalized for repository review."),
    ("permission_risk_report.md", "Permission Auditor findings and review summary."),
    ("human_permission_review_required.md", "Permission-specific human review queue."),
    ("authz_matrix_report.md", "AuthZ Matrix inferred/contract diff report."),
    ("authz_matrix_diff.json", "AuthZ Matrix expected-vs-observed diff data."),
    ("authz_negative_test_plan.md", "Suggested negative authorization tests."),
]


def _copy_review_artifacts(run_dir, pack_root):
    review_dir = os.path.join(pack_root, "REVIEW")
    os.makedirs(review_dir, exist_ok=True)
    rows = []
    for rel, purpose in REVIEW_ARTIFACTS:
        src = os.path.join(run_dir, rel)
        dst = os.path.join(review_dir, rel)
        if os.path.isfile(src):
            try:
                with open(src, "rb") as fi, open(dst, "wb") as fo:
                    fo.write(fi.read())
                rows.append({"path": rel, "purpose": purpose, "status": "available"})
            except Exception:
                rows.append({"path": rel, "purpose": purpose, "status": "missing"})
        else:
            rows.append({"path": rel, "purpose": purpose, "status": "missing"})
    return rows


def _review_outputs(rows):
    outputs = {
        "review_section": "context_pack/REVIEW/",
        "review_readme": "context_pack/REVIEW/README.md",
        "ai_maintenance_constraints": "context_pack/REVIEW/ai_maintenance_constraints.md",
    }
    key_map = {
        "repository_review_report.md": "repository_review_report",
        "review_risk_matrix.json": "review_risk_matrix",
        "human_review_required.md": "human_review_required",
        "backend_verifier_report.md": "backend_verifier_report",
        "code_health_summary.json": "code_health_summary",
        "maintainability_risks.json": "maintainability_risks",
        "permission_risk_report.md": "permission_risk_report",
        "human_permission_review_required.md": "human_permission_review_required",
        "authz_matrix_report.md": "authz_matrix_report",
        "authz_matrix_diff.json": "authz_matrix_diff",
        "authz_negative_test_plan.md": "authz_negative_test_plan",
    }
    for row in rows:
        if row.get("status") == "available":
            outputs[key_map[row["path"]]] = "context_pack/REVIEW/" + row["path"]
    return outputs


def _write_review_readme(run_dir, pack_root, rows):
    review_dir = os.path.join(pack_root, "REVIEW")
    lines = [
        "# Repository Review Context",
        "",
        "## What this section is",
        "",
        "This REVIEW section packages the evidence-backed review outputs that should be read before the next AI-assisted maintenance or upgrade.",
        "",
        "## Recommended reading order",
        "",
        "1. repository_review_report.md",
        "2. human_review_required.md",
        "3. backend_verifier_report.md",
        "4. code_health_summary.json",
        "5. permission_risk_report.md",
        "6. authz_matrix_report.md",
        "7. authz_negative_test_plan.md",
        "8. ai_maintenance_constraints.md",
        "",
        "## Available review artifacts",
        "",
        "path | purpose | status",
        "--- | --- | ---",
    ]
    for row in rows:
        lines.append(f"{row['path']} | {row['purpose']} | {row['status']}")
    lines += [
        "",
        "## Boundaries",
        "",
        "- This is not a correctness proof.",
        "- This does not replace human code review.",
        "- Suspected findings require human confirmation.",
        "- AI assistants should not make broad changes without checking human_review_required.md.",
        "",
        "## Suggested use",
        "",
        "- Use this section before asking an AI assistant to modify the repository.",
        "- Use human_review_required.md to identify risky areas.",
        "- Use authz_negative_test_plan.md before changing permission-sensitive code.",
        "- Use backend_verifier_report.md before modifying side-effect-heavy code.",
        "",
    ]
    with open(os.path.join(review_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _top_review_files(run_dir):
    out = []
    for rel, artifact, reason_key in [
        ("human_review_required.md", "human_review_required.md", "human review required"),
        ("maintainability_risks.json", "maintainability_risks.json", "code health risk"),
        ("permission_risks.json", "permission_risks.json", "permission risk"),
        ("authz_matrix_diff.json", "authz_matrix_diff.json", "authz matrix diff"),
    ]:
        obj = _read_json(os.path.join(run_dir, rel), {})
        rows = []
        if isinstance(obj, dict):
            rows = obj.get("risks") or obj.get("diffs") or []
        for row in rows[:5]:
            path = row.get("file") or ((row.get("route") or {}).get("path")) or ""
            reason = row.get("reason") or row.get("title") or reason_key
            if path:
                out.append({"file": path, "reason": reason, "artifact": artifact})
        if len(out) >= 10:
            break
    return out[:10]


def _write_ai_maintenance_constraints(run_dir, pack_root):
    review_dir = os.path.join(pack_root, "REVIEW")
    lines = [
        "# AI Maintenance Constraints",
        "",
        "## Before modifying code",
        "",
        "- Read repository_review_report.md first.",
        "- Check human_review_required.md before editing high-risk files.",
        "- Do not assume missing evidence means absence of risk.",
        "- Do not remove guards, transactions, queue consumers, or audit-related code without review.",
        "- Treat suspected permission findings as requiring human confirmation.",
        "- Preserve Context Pack / Run Manifest / evidence outputs when changing analysis logic.",
        "",
        "## High-risk areas",
        "",
    ]
    top = _top_review_files(run_dir)
    if top:
        for item in top:
            lines.append(f"- file: {item['file']}")
            lines.append(f"  - reason: {item['reason']}")
            lines.append(f"  - related artifact: {item['artifact']}")
            lines.append("  - suggested human decision: confirm before modifying this area")
    else:
        lines.append("- No high-risk review files were available in generated review artifacts.")
    lines += [
        "",
        "## Safe AI-assisted workflow",
        "",
        "1. Read REVIEW/README.md.",
        "2. Inspect human_review_required.md.",
        "3. Identify affected files.",
        "4. Make narrow changes.",
        "5. Re-run RepoSense.",
        "6. Compare reports / run manifest.",
        "7. Do not claim correctness without evidence.",
        "",
    ]
    with open(os.path.join(review_dir, "ai_maintenance_constraints.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


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
    _ensure_dirs(pack_root, ["MAP", "SPEC", "EVIDENCE/top_findings", "EVIDENCE/top_events", "ARTIFACTS", "REVIEW"])
    rep = _read_json(os.path.join(run_dir, "report.json"), {})
    cov = _read_json(os.path.join(run_dir, "coverage.json"), {})
    graph = _read_json(os.path.join(run_dir, "event_graph.json"), {"nodes": [], "edges": []})
    run_sum = rep.get("run_summary") or {}
    # copy artifacts
    for nm in ["report.json", "event_graph.json", "language_capabilities.json", "api_callers.json", "cross_language_summary.json", "patterns.json", "pattern_summary.json", "transaction_correlations.json", "transaction_correlation_summary.json", "typescript_transaction_validation.json", "typescript_transaction_validation.md", "route_intent_annotations.json", "file_context_annotations.json", "review_context_summary.json", "queue_cache_validation.json", "queue_cache_validation.md", "queue_reliability_correlations.json", "queue_reliability_summary.json", "queue_reliability_risks.json", "queue_retry_idempotency_validation.json", "queue_retry_idempotency_validation.md", "typeorm_db_operations.json", "typeorm_db_summary.json", "typeorm_db_validation.json", "typeorm_db_validation.md", "ai_summary.json", "ai_summary.md", "code_health.json", "code_health_summary.json", "maintainability_risks.json", "permission_surface.json", "permission_risks.json", "permission_risk_report.md", "human_permission_review_required.md", "authz_negative_test_plan.md", "authz_matrix_loaded.json", "authz_matrix_inferred.yaml", "authz_matrix_diff.json", "authz_matrix_report.md"]:
        src = os.path.join(run_dir, nm)
        dst = os.path.join(pack_root, "ARTIFACTS", nm)
        if os.path.isfile(src):
            try:
                if nm.endswith(".json"):
                    with open(src, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    with open(dst, "w", encoding="utf-8") as f2:
                        json.dump(data, f2, ensure_ascii=False)
                else:
                    with open(src, "rb") as f, open(dst, "wb") as f2:
                        f2.write(f.read())
            except Exception:
                pass
    for nm in [
        "route_guard_correlations.json",
        "route_guard_summary.json",
        "openapi_security_surface.json",
        "route_decorator_classifications.json",
        "route_decorator_summary.json",
    ]:
        src = os.path.join(run_dir, nm)
        dst = os.path.join(pack_root, "ARTIFACTS", nm)
        if os.path.isfile(src):
            with open(src, "r", encoding="utf-8") as f:
                data = json.load(f)
            with open(dst, "w", encoding="utf-8") as f2:
                json.dump(data, f2, ensure_ascii=False)
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
    review_rows = _copy_review_artifacts(run_dir, pack_root)
    _write_review_readme(run_dir, pack_root, review_rows)
    _write_ai_maintenance_constraints(run_dir, pack_root)
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
            "transaction_correlations": "context_pack/ARTIFACTS/transaction_correlations.json",
            "transaction_correlation_summary": "context_pack/ARTIFACTS/transaction_correlation_summary.json",
            "route_intent_annotations": "context_pack/ARTIFACTS/route_intent_annotations.json",
            "file_context_annotations": "context_pack/ARTIFACTS/file_context_annotations.json",
            "review_context_summary": "context_pack/ARTIFACTS/review_context_summary.json",
            **{
                key: f"context_pack/ARTIFACTS/{name}"
                for key, name in {
                    "route_guard_correlations": "route_guard_correlations.json",
                    "route_guard_summary": "route_guard_summary.json",
                    "openapi_security_surface": "openapi_security_surface.json",
                    "route_decorator_classifications": "route_decorator_classifications.json",
                    "route_decorator_summary": "route_decorator_summary.json",
                    "queue_cache_validation": "queue_cache_validation.json",
                    "queue_cache_validation_report": "queue_cache_validation.md",
                    "queue_reliability_correlations": "queue_reliability_correlations.json",
                    "queue_reliability_summary": "queue_reliability_summary.json",
                    "queue_reliability_risks": "queue_reliability_risks.json",
                    "queue_retry_idempotency_validation": "queue_retry_idempotency_validation.json",
                    "queue_retry_idempotency_validation_report": "queue_retry_idempotency_validation.md",
                    "typeorm_db_operations": "typeorm_db_operations.json",
                    "typeorm_db_summary": "typeorm_db_summary.json",
                    "typeorm_db_validation": "typeorm_db_validation.json",
                    "typeorm_db_validation_report": "typeorm_db_validation.md",
                    "typescript_transaction_validation": "typescript_transaction_validation.json",
                    "typescript_transaction_validation_report": "typescript_transaction_validation.md",
                }.items()
                if os.path.isfile(os.path.join(pack_root, "ARTIFACTS", name))
            },
            "ai_summary_json": "ai_summary.json",
            "ai_summary_md": "ai_summary.md",
            "code_health": "context_pack/ARTIFACTS/code_health.json",
            "code_health_summary": "context_pack/ARTIFACTS/code_health_summary.json",
            "maintainability_risks": "context_pack/ARTIFACTS/maintainability_risks.json",
            "permission_surface": "context_pack/ARTIFACTS/permission_surface.json",
            "permission_risks": "context_pack/ARTIFACTS/permission_risks.json",
            "permission_risk_report": "context_pack/ARTIFACTS/permission_risk_report.md",
            "human_permission_review": "context_pack/ARTIFACTS/human_permission_review_required.md",
            "authz_negative_test_plan": "context_pack/ARTIFACTS/authz_negative_test_plan.md",
            "authz_matrix_loaded": "context_pack/ARTIFACTS/authz_matrix_loaded.json",
            "authz_matrix_inferred": "context_pack/ARTIFACTS/authz_matrix_inferred.yaml",
            "authz_matrix_diff": "context_pack/ARTIFACTS/authz_matrix_diff.json",
            "authz_matrix_report": "context_pack/ARTIFACTS/authz_matrix_report.md",
            "api_topology": "context_pack/MAP/api_topology.json",
            "api_surface": "api_surface.json",
            "learn_base": "learn/",
            "exports": "exports/",
            "context_pack": "context_pack/",
            "baseline_in": "baseline_in.json",
            "baseline_diff_json": "baseline_diff.json",
            "baseline_diff_md": "baseline_diff.md",
            **_review_outputs(review_rows),
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
        tcs = _read_json(os.path.join(run_dir, "transaction_correlation_summary.json"), {})
        if isinstance(tcs, dict) and tcs:
            counts = tcs.get("counts_by_coverage_status") or {}
            readme.append("")
            readme.append("## Transaction Correlation")
            readme.append(f"- total correlations: {int(tcs.get('total_correlations') or 0)}")
            readme.append(f"- covered / uncovered: {int(counts.get('covered_explicit') or 0)} / {int(counts.get('uncovered') or 0)}")
            readme.append(f"- partial / unknown / read-only: {int(counts.get('partially_covered') or 0)} / {int(counts.get('unknown') or 0)} / {int(counts.get('read_only_transaction') or 0)}")
            readme.append("- files: ARTIFACTS/transaction_correlations.json, ARTIFACTS/transaction_correlation_summary.json")
            by_runtime = tcs.get("by_language_framework") or {}
            typescript = by_runtime.get("typescript/typeorm") or {}
            if typescript:
                mechanisms = typescript.get("counts_by_transaction_mechanism") or {}
                readme.append(
                    "- TypeScript callback / QueryRunner / decorator / wrapper: "
                    f"{int(mechanisms.get('typeorm_callback') or 0) + int(mechanisms.get('entity_manager_callback') or 0)} / "
                    f"{int(mechanisms.get('query_runner') or 0)} / "
                    f"{int(mechanisms.get('trusted_decorator_method') or 0) + int(mechanisms.get('trusted_decorator_class') or 0)} / "
                    f"{int(mechanisms.get('direct_wrapper_caller') or 0)}"
                )
    except Exception:
        pass
    try:
        rcs = _read_json(os.path.join(run_dir, "review_context_summary.json"), {})
        if isinstance(rcs, dict) and rcs:
            readme.append("")
            readme.append("## Review Context Calibration")
            readme.append(f"- public auth entrypoints: {int(rcs.get('public_auth_route_count') or 0)}")
            readme.append(f"- findings downweighted / excluded: {int(rcs.get('findings_downweighted_count') or 0)} / {int(rcs.get('findings_excluded_from_primary_review_count') or 0)}")
            readme.append("- files: ARTIFACTS/route_intent_annotations.json, ARTIFACTS/file_context_annotations.json, ARTIFACTS/review_context_summary.json")
    except Exception:
        pass
    try:
        rgs = _read_json(os.path.join(run_dir, "route_guard_summary.json"), {})
        if isinstance(rgs, dict) and rgs:
            readme.append("")
            readme.append("## Route Guard Correlation")
            readme.append(
                "- protected method / controller / global routes: "
                f"{int(rgs.get('protected_method') or 0)} / "
                f"{int(rgs.get('protected_controller') or 0)} / "
                f"{int(rgs.get('protected_global') or 0)}"
            )
            readme.append(
                "- intentional public bypasses: "
                f"{int(rgs.get('intentional_public_bypasses') or 0)}"
            )
            readme.append(
                "- OpenAPI protected without code guard: "
                f"{int(rgs.get('openapi_protected_without_code_guard') or 0)}"
            )
            readme.append(
                "- OpenAPI security is contract evidence, not implementation guard proof."
            )
            readme.append(
                "- files: ARTIFACTS/route_guard_correlations.json, "
                "ARTIFACTS/route_guard_summary.json, "
                "ARTIFACTS/openapi_security_surface.json"
            )
    except Exception:
        pass
    try:
        rds = _read_json(os.path.join(run_dir, "route_decorator_summary.json"), {})
        if isinstance(rds, dict) and rds:
            readme.append("")
            readme.append("## Route Decorator Classification")
            readme.append(
                "- accepted routes / rejected non-routes / unknown: "
                f"{int(rds.get('accepted_route_count') or 0)} / "
                f"{int(rds.get('rejected_non_route_count') or 0)} / "
                f"{int(rds.get('unknown_count') or 0)}"
            )
            readme.append(
                "- files: ARTIFACTS/route_decorator_classifications.json, "
                "ARTIFACTS/route_decorator_summary.json"
            )
    except Exception:
        pass
    try:
        qcv = _read_json(
            os.path.join(run_dir, "queue_cache_validation.json"),
            {},
        )
        qcs = qcv.get("summary") if isinstance(qcv.get("summary"), dict) else {}
        if qcs:
            readme.append("")
            readme.append("## Queue / Cache Validation")
            readme.append(
                "- dispatch / consume / matched pairs: "
                f"{int(qcs.get('queue_dispatch_count') or 0)} / "
                f"{int(qcs.get('queue_consume_count') or 0)} / "
                f"{int(qcs.get('matched_producer_consumer_pairs') or 0)}"
            )
            readme.append(
                "- unmatched dispatch / unresolved names: "
                f"{int(qcs.get('unmatched_dispatches') or 0)} / "
                f"{int(qcs.get('unknown_name_events') or 0)}"
            )
            readme.append(
                "- cache read / write / invalidate: "
                f"{int(qcs.get('cache_read_count') or 0)} / "
                f"{int(qcs.get('cache_write_count') or 0)} / "
                f"{int(qcs.get('cache_invalidate_count') or 0)}"
            )
            readme.append(
                "- files: ARTIFACTS/queue_cache_validation.json, "
                "ARTIFACTS/queue_cache_validation.md"
            )
    except Exception:
        pass
    try:
        reliability = _read_json(
            os.path.join(run_dir, "queue_reliability_summary.json"),
            {},
        )
        if reliability:
            readme.append("")
            readme.append("## Queue Reliability")
            readme.append(
                "- matched channels / explicit retries: "
                f"{int(reliability.get('matched_channels') or 0)} / "
                f"{int(reliability.get('explicit_retries') or 0)}"
            )
            readme.append(
                "- retry with guard / producer dedupe only / without guard: "
                f"{int(reliability.get('retry_with_consumer_guard') or 0)} / "
                f"{int(reliability.get('retry_with_producer_dedupe_only') or 0)} / "
                f"{int(reliability.get('retry_without_consumer_guard') or 0)}"
            )
            readme.append(
                "- Producer identity does not prove consumer business idempotency."
            )
            readme.append(
                "- files: ARTIFACTS/queue_reliability_correlations.json, "
                "ARTIFACTS/queue_reliability_summary.json, "
                "ARTIFACTS/queue_reliability_risks.json"
            )
    except Exception:
        pass
    try:
        typeorm = _read_json(
            os.path.join(run_dir, "typeorm_db_summary.json"),
            {},
        )
        if typeorm:
            readme.append("")
            readme.append("## TypeORM DB Coverage")
            readme.append(
                "- reads / writes / transactions: "
                f"{int(typeorm.get('db_reads') or 0)} / "
                f"{int(typeorm.get('db_writes') or 0)} / "
                f"{int(typeorm.get('db_transactions') or 0)}"
            )
            readme.append(
                "- explicit / unresolved write transaction context: "
                f"{int(typeorm.get('writes_with_explicit_transaction_context') or 0)} / "
                f"{int(typeorm.get('writes_with_unresolved_transaction_coverage') or 0)}"
            )
            readme.append(
                "- files: ARTIFACTS/typeorm_db_operations.json, "
                "ARTIFACTS/typeorm_db_summary.json"
            )
    except Exception:
        pass
    try:
        if os.path.isfile(os.path.join(run_dir, "ai_summary.md")):
            readme.append("")
            readme.append("## AI Summary")
            readme.append("- file: ARTIFACTS/ai_summary.md")
    except Exception:
        pass
    try:
        chs = _read_json(os.path.join(run_dir, "code_health_summary.json"), {})
        if isinstance(chs, dict) and chs:
            readme.append("")
            readme.append("## Code Health Summary")
            readme.append(f"- total findings: {int(chs.get('total_findings') or 0)}")
            score = (chs.get("health_score") or {}).get("score")
            readme.append(f"- experimental health score: {int(score or 0)}")
            cbr = chs.get("counts_by_rule") or {}
            if cbr:
                readme.append("- counts by rule: " + ", ".join([f"{k}:{v}" for k, v in sorted(cbr.items(), key=lambda x: x[0])]))
            readme.append("- file: ARTIFACTS/code_health_summary.json")
    except Exception:
        pass
    try:
        prs = _read_json(os.path.join(run_dir, "permission_risks.json"), {})
        risks = prs.get("risks") if isinstance(prs.get("risks"), list) else []
        if isinstance(prs, dict) and prs:
            readme.append("")
            readme.append("## Permission Review Summary")
            readme.append(f"- total permission risks: {len(risks)}")
            high = len([r for r in risks if str(r.get("severity") or "") == "high"])
            medium = len([r for r in risks if str(r.get("severity") or "") == "medium"])
            readme.append(f"- high / medium: {high} / {medium}")
            readme.append("- file: ARTIFACTS/permission_risks.json")
    except Exception:
        pass
    try:
        azd = _read_json(os.path.join(run_dir, "authz_matrix_diff.json"), {})
        if isinstance(azd, dict) and azd:
            readme.append("")
            readme.append("## AuthZ Matrix Summary")
            readme.append(f"- mode: {azd.get('mode')}")
            sm = azd.get("summary") or {}
            readme.append(f"- missing auth: {int(sm.get('missing_auth') or 0)}")
            readme.append(f"- missing permission: {int(sm.get('missing_permission') or 0)}")
            readme.append("- file: ARTIFACTS/authz_matrix_diff.json")
    except Exception:
        pass
    try:
        rr = _read_json(os.path.join(run_dir, "repository_review_report.json"), {})
        rm_obj = _read_json(os.path.join(run_dir, "review_risk_matrix.json"), {})
        chs = _read_json(os.path.join(run_dir, "code_health_summary.json"), {})
        prs = _read_json(os.path.join(run_dir, "permission_risks.json"), {})
        azd = _read_json(os.path.join(run_dir, "authz_matrix_diff.json"), {})
        readme.append("")
        readme.append("## Repository Review Section")
        readme.append("The REVIEW/ directory contains evidence-backed review outputs for the next AI-assisted maintenance or upgrade.")
        readme.append(f"- review decision: {rm_obj.get('decision') or ((rr.get('review_summary') or {}).get('decision')) or 'not available'}")
        readme.append(f"- human review required count: {int(((rr.get('review_summary') or {}).get('human_review_required_count')) or (rm_obj.get('human_review_required_count') or 0))}")
        readme.append(f"- code health risk count: {int(chs.get('total_findings') or 0) if isinstance(chs, dict) else 0}")
        perm_risks = prs.get("risks") if isinstance(prs.get("risks"), list) else []
        readme.append(f"- permission risk count: {len(perm_risks)}")
        readme.append(f"- AuthZ matrix mode: {azd.get('mode') or 'not available'}")
        readme.append("- key limitations: not a correctness proof; suspected findings require human confirmation; review context does not replace human code review")
        readme.append("- entry: REVIEW/README.md")
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
