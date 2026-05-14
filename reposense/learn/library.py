import os
import json
from pathlib import Path
from .extract_cases import _case_id
from .case_extractor import extract_cases
from .concept_graph import load_concept_graph, ConceptGraph
def _atomic_write_json(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f)
    os.replace(tmp, p)
def library_init(lib_dir):
    outp = Path(lib_dir).resolve()
    outp.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(str(outp / "lib_manifest.json"), {"version":"1.0"})
    (outp / "runs").mkdir(exist_ok=True)
    _atomic_write_json(str(outp / "case_index.json"), {})
    _atomic_write_json(str(outp / "casebank.jsonl"), [])
def library_add(run_dir, lib_dir, min_conf, graph_path, map_path=None):
    outp = Path(lib_dir).resolve()
    # read existing casebank
    cb_path = outp / "casebank.jsonl"
    existing = {}
    if cb_path.exists():
        for ln in cb_path.read_text(encoding="utf-8").splitlines():
            if not ln.strip(): continue
            try:
                item = json.loads(ln)
                existing.setdefault(item["case_id"], item)
            except:
                pass
    cg = ConceptGraph(load_concept_graph(graph_path))
    cases = [c for c in extract_cases(run_dir) if float(c.get("confidence",0.0)) >= float(min_conf)]
    # append run summary
    _atomic_write_json(str(outp / "runs" / (Path(run_dir).name + ".json")), {"run_dir": run_dir})
    # merge cases
    for c in cases:
        info = cg.get(c["concept"])
        concept_id = (info.get("concept_id") if info else c["concept"])
        cid = _case_id(c, concept_id)
        src = {"run_id": Path(run_dir).name, "primary_eid": c.get("primary_eid"), "confidence": c.get("confidence"), "evidence_refs": c["evidence_refs"]}
        if cid in existing:
            existing[cid].setdefault("sources", []).append(src)
        else:
            existing[cid] = {"case_id": cid, "concept_id": concept_id, "level": c["difficulty"], "rule_id": c.get("rule_id"), "confidence": c.get("confidence"), "sources": [src]}
    # write back casebank.jsonl
    lines = [json.dumps(existing[k]) for k in sorted(existing.keys())]
    tmp = cb_path.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")
    os.replace(tmp, cb_path)
def library_stats(lib_dir):
    outp = Path(lib_dir).resolve()
    cb_path = outp / "casebank.jsonl"
    count = 0
    by_concept = {}
    if cb_path.exists():
        for ln in cb_path.read_text(encoding="utf-8").splitlines():
            if not ln.strip(): continue
            item = json.loads(ln)
            count += 1
            by_concept[item["concept_id"]] = by_concept.get(item["concept_id"], 0) + 1
    return {"cases": count, "by_concept": by_concept}
def library_verify(lib_dir):
    outp = Path(lib_dir).resolve()
    cb_path = outp / "casebank.jsonl"
    errors = []
    if cb_path.exists():
        for ln in cb_path.read_text(encoding="utf-8").splitlines():
            if not ln.strip(): continue
            item = json.loads(ln)
            sources = item.get("sources") or []
            if not sources:
                errors.append("missing sources")
            for s in sources:
                if not s.get("evidence_refs"):
                    errors.append("source missing evidence_refs")
    return {"ok": len(errors)==0, "errors": errors}
