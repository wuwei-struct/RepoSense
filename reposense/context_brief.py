import os
import json
import re
from pathlib import Path
def _load_json(path):
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.load(open(p, "r", encoding="utf-8"))
    except:
        return None
def _atomic_write(path, text):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, p)
def _sha256_file(fp):
    import hashlib
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
def build_brief(run_dir, out_dir, max_items=20, as_json=False):
    rd = Path(run_dir)
    od = Path(out_dir).resolve()
    od.mkdir(parents=True, exist_ok=True)
    warnings = []
    manifest = _load_json(rd/"manifest.json") or {}
    meta_cfg = _load_json(rd/"meta"/"config.json") or {}
    snapshot = _load_json(rd/"snapshot.json") or {}
    arch_dir = rd/"arch_views"
    api_surface = _load_json(arch_dir/"api_surface.json") or {"items":[]}
    service_map = _load_json(arch_dir/"service_map.json") or {"services":[],"infra":[],"edges":[]}
    data_surface = _load_json(arch_dir/"data_surface.json") or {"tables":[],"indexes":[]}
    async_surface = _load_json(arch_dir/"async_surface.json") or {"workflows":[],"schedulers":[],"queues":[]}
    report = _load_json(rd/"report.json") or {}
    if snapshot is None:
        warnings.append("missing_snapshot")
        snapshot = {"events": [], "findings": [], "stats": {}}
    if not arch_dir.exists():
        warnings.append("missing_arch_views")
    used_eids = set()
    def ev_line(eids):
        for e in eids:
            used_eids.add(str(e))
        return "Evidence: " + ", ".join([str(e) for e in eids])
    # Repo Fingerprint
    fp = _load_json(rd/"repo_fingerprint.json") or {}
    # What this pack contains
    pack_files = []
    for root, dirs, files in os.walk(rd):
        # only list top-level artifacts and arch/evidence files count
        break
    # System at a glance
    stats = snapshot.get("stats", {})
    # API Surface
    apis = api_surface.get("items", [])
    apis = sorted(apis, key=lambda x: (x.get("method",""), x.get("path","")))[:max_items]
    # Service & Infra Dependencies
    edges = service_map.get("edges", [])
    edges = sorted(edges, key=lambda x: (x.get("from",""), x.get("to","")))[:max_items]
    # Data Surface
    tables = sorted(data_surface.get("tables", []), key=lambda x: x.get("name",""))[:max_items]
    indexes = sorted(data_surface.get("indexes", []), key=lambda x: x.get("name",""))[:max_items]
    # Async/Workflow
    workflows = sorted(async_surface.get("workflows", []), key=lambda x: x.get("workflow_path",""))[:max_items]
    schedulers = sorted(async_surface.get("schedulers", []), key=lambda x: x.get("kind",""))[:max_items]
    queues = sorted(async_surface.get("queues", []), key=lambda x: x.get("infra_kind",""))[:max_items]
    # Findings Summary
    findings = snapshot.get("findings", [])
    by_concept = {}
    for f in findings:
        by_concept.setdefault(f.get("concept",""), []).append(f)
    for k in by_concept:
        by_concept[k] = sorted(by_concept[k], key=lambda x: (-float(x.get("confidence",0.0)), x.get("fid",0)))[:max_items]
    # Build Markdown
    md = []
    md.append("# Repo Context Brief")
    md.append("## Repo Fingerprint")
    md.append(f"- mode: {fp.get('mode','')}")
    if fp.get("mode") == "git":
        md.append(f"- head: {fp.get('head','')}")
    md.append("## What this pack contains")
    md.append("- snapshot.json, arch_views/, report.json, event_graph.json, evidence/")
    md.append("## System at a glance")
    md.append(f"- files_count: {stats.get('files_count',0)}")
    md.append(f"- concept_counts: {json.dumps(stats.get('concept_counts',{}))}")
    md.append("## API Surface")
    for a in apis:
        line = f"- {a.get('method','')} {a.get('path','')} conf={a.get('confidence',0.0)} src={a.get('source','')}"
        md.append(line)
        md.append(ev_line(a.get("evidence", [])))
    md.append("## Service & Infra Dependencies")
    for e in edges:
        md.append(f"- {e.get('from')} -> {e.get('to')} type={e.get('type')}")
        md.append(ev_line(e.get("evidence", [])))
    md.append("## Data Surface")
    for t in tables:
        md.append(f"- table {t.get('name')}")
        md.append(ev_line(t.get("evidence", [])))
    for ix in indexes:
        md.append(f"- index {ix.get('name')}")
        md.append(ev_line(ix.get("evidence", [])))
    md.append("## Async / Workflow")
    for w in workflows:
        md.append(f"- workflow {w.get('workflow_path')}")
        md.append(ev_line(w.get("evidence", [])))
    for s in schedulers:
        md.append(f"- scheduler {s.get('kind')}")
        md.append(ev_line(s.get("evidence", [])))
    for q in queues:
        md.append(f"- queue {q.get('infra_kind')}")
        md.append(ev_line(q.get("evidence", [])))
    md.append("## Findings Summary")
    concepts_sorted = sorted(by_concept.keys())
    for c in concepts_sorted:
        md.append(f"### {c}")
        for f in by_concept[c]:
            md.append(f"- fid {f.get('fid')} conf={f.get('confidence',0.0)}")
            eid = f.get("primary_eid")
            if eid is not None:
                md.append(ev_line([f"E{eid}"]))
    # Evidence Index
    md.append("## Evidence Index")
    # ensure only E-prefixed
    ev_ids = sorted(set([e if str(e).startswith("E") else f"E{e}" for e in used_eids]))
    md.append(", ".join(ev_ids))
    # Notes & Uncertainty
    md.append("## Notes & Uncertainty")
    if warnings:
        md.append("NEEDS_CONFIRMATION: " + ", ".join(warnings))
    else:
        md.append("None")
    brief_md = "\n".join(md)
    _atomic_write(od/"context_brief.md", brief_md)
    # structured JSON (optional)
    brief_json = {
        "fingerprint": fp,
        "stats": stats,
        "api_top": apis,
        "service_edges_top": edges,
        "tables_top": tables,
        "indexes_top": indexes,
        "workflows_top": workflows,
        "schedulers_top": schedulers,
        "queues_top": queues,
        "findings_top": by_concept,
        "evidence_index": ev_ids,
        "warnings": warnings
    }
    with open(od/"context_brief.json", "w", encoding="utf-8") as f:
        json.dump(brief_json, f)
    with open(od/"brief_warnings.json", "w", encoding="utf-8") as f:
        json.dump(warnings, f)
    # validate evidence existence
    missing = []
    for e in ev_ids:
        p = rd/"evidence"/f"{e}.json"
        if not p.exists():
            missing.append(e)
    if missing:
        warnings.append("missing_evidence_in_brief")
        with open(od/"brief_warnings.json", "w", encoding="utf-8") as f:
            json.dump(warnings, f)
    if as_json:
        print(json.dumps({"ok": True, "out_dir": str(od), "evidence_count": len(ev_ids), "warnings": warnings}))
    return str(od)
