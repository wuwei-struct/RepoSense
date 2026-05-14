import os
import json
import hashlib
from pathlib import Path
from .concept_graph import load_concept_graph, ConceptGraph, default_concept_graph_path
from .run_reader import open_run
from ..shared.case_library.store import CaseLibraryStore


def _sha12(s): return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]


def _case_id(case, concept_id):
    e = case["evidence_refs"][0] if case["evidence_refs"] else {"path":"", "start_line":0, "end_line":0, "parse_level":""}
    repo_ref = str(case.get("repo_ref") or "")
    primary = str(e.get("eid") or case.get("primary_eid") or "")
    parts = [repo_ref, primary, str(case.get("rule_id") or ""), str(concept_id), str(e.get("path")), str(e.get("start_line")), str(e.get("end_line"))]
    return _sha12("|".join(parts))


def _atomic_write(out_path, data_lines):
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for line in data_lines:
            f.write(line + "\n")
    os.replace(tmp, p)


def _meta_text(meta):
    try:
        return json.dumps(meta or {}, ensure_ascii=False).lower()
    except Exception:
        return str(meta or "").lower()


def _snippet_text(evid):
    out = []
    for e in evid or []:
        out.append(str(e.get("snippet") or ""))
    return "\n".join(out).lower()


def _determine_language(meta, evid):
    lg = str((meta or {}).get("language") or "").lower()
    if lg:
        return lg
    p = str((evid or [{}])[0].get("path") or "").lower()
    if p.endswith(".py"):
        return "python"
    if p.endswith((".ts", ".tsx", ".mts", ".cts")):
        return "typescript"
    if p.endswith(".java"):
        return "java"
    if p.endswith(".sql"):
        return "sql"
    return "unknown"


def _level_by_context(kind, f, file_signals):
    path = str((f.get("evidence_refs") or [{}])[0].get("path") or "")
    sig = file_signals.get(path, {"has_db": False, "has_queue": False, "has_api": False, "has_tx": False})
    if kind == "data.transaction_boundary":
        if sig["has_db"] and (sig["has_queue"] or sig["has_api"]):
            return 3
        if sig["has_db"]:
            return 2
        return 1
    if kind == "reliability.idempotency":
        if sig["has_tx"] and sig["has_db"] and (sig["has_queue"] or sig["has_api"]):
            return 3
        if sig["has_tx"] or (sig["has_db"] and sig["has_queue"]):
            return 2
        return 1
    if kind == "concurrency.locking_or_guard":
        if sig["has_tx"] and sig["has_db"]:
            return 3
        if sig["has_tx"] or sig["has_db"]:
            return 2
        return 1
    return 1


def _build_file_signals(rh):
    file_signals = {}
    for ev in rh.iter_events():
        m = ev.get("meta") or {}
        p = str(m.get("path") or "")
        if not p:
            continue
        s = file_signals.setdefault(p, {"has_db": False, "has_queue": False, "has_api": False, "has_tx": False})
        tp = str(ev.get("type") or "")
        if tp in ("db_op", "tx_boundary"):
            s["has_db"] = True
        if tp == "db_op":
            s["has_db"] = True
        if tp in ("queue_dispatch", "queue_consume"):
            s["has_queue"] = True
        if tp == "api":
            s["has_api"] = True
        if tp == "tx_boundary":
            s["has_tx"] = True
    return file_signals


def _grounded_fields(concept_id, evidence_refs):
    ev = evidence_refs[0] if evidence_refs else {}
    where = f"{ev.get('path','')}:{ev.get('start_line',0)}-{ev.get('end_line',0)}"
    if concept_id == "data.transaction_boundary":
        what = f"在 {where} 发现显式事务边界证据。"
        why = "事务边界属于一致性核心机制，可保证多步操作原子性。"
        how = "通过框架事务注解或事务语句将一组操作纳入同一提交/回滚边界。"
        risk = "缺失事务边界会导致部分成功、部分失败，出现脏状态。"
    elif concept_id == "reliability.idempotency":
        what = f"在 {where} 发现防重复或去重保护线索。"
        why = "幂等可以降低重试、重复投递和并发重入导致的重复副作用。"
        how = "通过 key/exists/guard/unique 等可复现保护模式限制重复执行。"
        risk = "缺少幂等保护会造成重复写入、重复扣费或重复消息处理。"
    else:
        what = f"在 {where} 发现并发保护证据。"
        why = "锁与并发保护用于控制共享资源竞争并避免竞态。"
        how = "通过 lock/mutex/synchronized/guard/semaphore 或 for update 实施保护。"
        risk = "缺失并发保护会出现竞态、覆盖写与不一致读。"
    return what, why, how, risk


def _candidate_cases(run_dir):
    rh = open_run(run_dir)
    file_signals = _build_file_signals(rh)
    repo_ref = os.path.basename(os.path.abspath(run_dir))
    out = []
    for f in rh.iter_findings():
        evid = rh.get_finding_evidence(f["fid"])
        if not evid:
            continue
        meta = f.get("meta") or {}
        txt = (_snippet_text(evid) + "\n" + _meta_text(meta) + "\n" + str(f.get("rule_id") or "").lower() + "\n" + str(f.get("concept") or "").lower())
        concepts = []
        if "transaction" in txt or "tx." in txt or "transactional" in txt or str(f.get("concept") or "").lower() == "transaction":
            concepts.append("data.transaction_boundary")
        if any(k in txt for k in ["idempot", "dedup", "dedupe", "request key", "idempotency", "existsbefore", "existsbyid", "findbefore", "setnx", "unique"]):
            concepts.append("reliability.idempotency")
        if any(k in txt for k in [" lock", "mutex", "synchronized", "semaphore", "guard", "for update", "optimistic"]):
            concepts.append("concurrency.locking_or_guard")
        if not concepts:
            concepts.append(str(f.get("concept") or "").lower())
        for cid in concepts:
            c = {
                "concept": str(f.get("concept") or "").lower(),
                "concept_id": cid,
                "difficulty": 1,
                "fid": f["fid"],
                "rule_id": f.get("rule_id"),
                "confidence": float(f.get("confidence") or 0.0),
                "primary_eid": f.get("primary_eid"),
                "evidence_refs": evid,
                "repo_ref": repo_ref,
                "notes": {"meta_echo": meta},
                "language": _determine_language(meta, evid),
            }
            c["difficulty"] = _level_by_context(cid, c, file_signals)
            out.append(c)
    rh.close()
    out.sort(key=lambda x: (x["concept_id"], -float(x.get("confidence") or 0.0), str((x.get("evidence_refs") or [{}])[0].get("path") or ""), int((x.get("evidence_refs") or [{}])[0].get("start_line") or 0), str(x.get("rule_id") or ""), int(x.get("fid") or 0)))
    return out


def extract_cases_to_dir(run_dir, out_dir, min_confidence, concept_graph_path, as_json=False, case_spec=False):
    gpath = concept_graph_path or default_concept_graph_path()
    cg = ConceptGraph(load_concept_graph(gpath))
    valid_ids = set([str(c.get("concept_id") or c.get("concept") or c.get("name") or c.get("title") or "").lower() for c in (cg.graph.get("concepts") or []) if (c.get("concept_id") or c.get("concept") or c.get("name") or c.get("title"))])
    raw = _candidate_cases(run_dir)
    cases = [c for c in raw if float(c.get("confidence", 0.0)) >= float(min_confidence)]
    outp = Path(out_dir).resolve()
    outp.mkdir(parents=True, exist_ok=True)
    lines = []
    rich_cases = []
    for c in cases:
        info = cg.get(c.get("concept_id") or c.get("concept"))
        concept_id = (info.get("concept_id") if info else (c.get("concept_id") or c.get("concept")))
        if gpath == default_concept_graph_path() and valid_ids and str(concept_id).lower() not in valid_ids:
            continue
        cid = _case_id(c, concept_id)
        what, why, how, risk = _grounded_fields(concept_id, c["evidence_refs"])
        title = f"{(info or {}).get('name') or (info or {}).get('title') or concept_id} | {str(c.get('rule_id') or 'rule')}"
        rows = {
            "case_id": cid,
            "concept_id": concept_id,
            "level": c["difficulty"],
            "title": title,
            "repo_ref": c.get("repo_ref"),
            "rule_id": c.get("rule_id"),
            "confidence": c.get("confidence"),
            "evidence_refs": c["evidence_refs"],
            "explain": {"what": what, "why": why, "how": how, "risk": risk},
            "what": what,
            "why": why,
            "how": how,
            "risk": risk,
            "labels": [str(c.get("language") or "unknown"), f"level:{int(c.get('difficulty') or 1)}"],
            "metadata": {"language": c.get("language") or "unknown", "rule_id": c.get("rule_id") or "", "fid": c.get("fid"), "primary_eid": c.get("primary_eid"), "parse_levels": sorted(list(set([str(x.get("parse_level") or "") for x in (c.get("evidence_refs") or [])])))}
        }
        lines.append(json.dumps(rows))
        rich_cases.append(rows)
        if case_spec:
            ddir = outp / concept_id
            ddir.mkdir(parents=True, exist_ok=True)
            js = {
                "case_id": cid,
                "concept_id": concept_id,
                "finding_stable_id": cid,
                "level": c["difficulty"],
                "rule_id": c.get("rule_id"),
                "confidence": c.get("confidence"),
                "evidence_refs": c["evidence_refs"],
                "notes": c.get("notes",{})
            }
            with (ddir / f"finding_{cid}.case.json").open("w", encoding="utf-8") as f:
                json.dump(js, f)
    _atomic_write(str(outp / "casebank.jsonl"), lines)
    by_concept = {}
    for x in rich_cases:
        by_concept[x["concept_id"]] = by_concept.get(x["concept_id"], 0) + 1
    manifest = {
        "run_dir": run_dir,
        "min_confidence": min_confidence,
        "counts": {"cases": len(lines), "by_concept": by_concept},
        "warnings": []
    }
    with (outp / "case_manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f)
    store = CaseLibraryStore(str(outp))
    summary = {"run_dir": run_dir, "total_cases": len(rich_cases), "concept_counts": by_concept}
    store.write_cases(rich_cases, summary)
    if as_json:
        return {"ok": True, "counts": manifest["counts"], "out": str(outp)}


def run_extract_cases(run_dir, out_dir, min_confidence, concept_graph_path, as_json, case_spec=False):
    res = extract_cases_to_dir(run_dir, out_dir, min_confidence, concept_graph_path or default_concept_graph_path(), as_json, case_spec=case_spec)
    if as_json:
        print(json.dumps(res))
    else:
        print(out_dir)
