import os
import json
import zipfile
import tempfile
import shutil
import hashlib
import re
from pathlib import Path
from .diff import stable_finding_id
def _unpack_if_zip(path):
    p = Path(path)
    if p.is_dir():
        return str(p), None
    if p.suffix.lower() == ".zip":
        td = tempfile.mkdtemp(prefix="ctxdiff-")
        with zipfile.ZipFile(str(p), "r") as zf:
            zf.extractall(td)
        return td, td
    return str(p), None
def _read_json(path):
    try:
        return json.load(open(path, "r", encoding="utf-8"))
    except:
        return None
def _sha256_dir(d):
    base = Path(d).resolve()
    entries = {}
    for root, dirs, files in os.walk(base):
        for nm in sorted(files):
            fp = Path(root)/nm
            rel = str(fp.relative_to(base)).replace("\\","/")
            h = hashlib.sha256(open(fp, "rb").read()).hexdigest()
            entries[rel] = h
    return [{"path": k, "sha256": entries[k]} for k in sorted(entries.keys())]
def _collect_events(snap):
    return {(e.get("type"), e.get("key")) for e in snap.get("events", [])}
def _collect_findings_stable(pack_dir):
    # use detections.sqlite to compute stable ids
    import sqlite3
    conn = sqlite3.connect(str(Path(pack_dir) / "artifacts" / "detections.sqlite"))
    c = conn.cursor()
    rows = c.execute("select f.fid, f.concept, f.rule_id, e.parse_level, f.confidence, f.primary_eid, f.meta_json, e.path from findings f join evidence e on e.eid=f.primary_eid").fetchall()
    items = set()
    for fid, concept, rule_id, parse_level, confidence, primary_eid, meta_json, path in rows:
        m = {}
        try:
            m = json.loads(meta_json or "{}")
        except:
            m = {}
        sid, _ = stable_finding_id({"concept": concept, "rule_id": rule_id, "parse_level": parse_level, "confidence": confidence, "primary_eid": primary_eid, "meta": m, "evidence_path": path})
        items.add((concept, sid))
    try:
        conn.close()
    except:
        pass
    return items
def _collect_arch_items(pack_dir):
    av = Path(pack_dir)/"artifacts"/"arch_views"
    res = {}
    if not av.exists():
        return res
    def load(fp, key):
        data = _read_json(av/fp) or {}
        res[key] = data
    load("api_surface.json","api")
    load("service_map.json","svc")
    load("data_surface.json","data")
    load("async_surface.json","async")
    load("deps_surface.json","deps")
    return res
def _collect_data_from_db(pack_dir):
    import sqlite3
    tables = set()
    indexes = set()
    conn = sqlite3.connect(str(Path(pack_dir) / "artifacts" / "detections.sqlite"))
    c = conn.cursor()
    for fid, concept, meta_json in c.execute("select fid, concept, meta_json from findings").fetchall():
        try:
            m = json.loads(meta_json or "{}")
        except:
            m = {}
        if concept == "Storage":
            for t in m.get("table_names") or []:
                tables.add(str(t))
            for ix in m.get("index_names") or []:
                indexes.add(str(ix))
        if concept == "Index":
            for ix in m.get("index_names") or []:
                indexes.add(str(ix))
    try:
        conn.close()
    except:
        pass
    return tables, indexes
def _collect_brief_eids(pack_dir):
    bj = _read_json(Path(pack_dir)/"context_brief.json") or {}
    eids = bj.get("evidence_index")
    if eids:
        return set(eids)
    mdp = Path(pack_dir)/"context_brief.md"
    if mdp.exists():
        txt = mdp.read_text(encoding="utf-8")
        return set(re.findall(r"\bE\d+\b", txt))
    return set()
def build_context_diff(packA, packB, out_dir, as_json=False):
    a_dir, a_tmp = _unpack_if_zip(packA)
    b_dir, b_tmp = _unpack_if_zip(packB)
    od = Path(out_dir).resolve()
    od.mkdir(parents=True, exist_ok=True)
    warnings = []
    fpA = _read_json(Path(a_dir)/"repo_fingerprint.json") or {}
    fpB = _read_json(Path(b_dir)/"repo_fingerprint.json") or {}
    snapA = _read_json(Path(a_dir)/"snapshot.json") or {"events": [], "findings": []}
    snapB = _read_json(Path(b_dir)/"snapshot.json") or {"events": [], "findings": []}
    evA = _collect_events(snapA); evB = _collect_events(snapB)
    events_added = sorted(list(evB - evA))
    events_removed = sorted(list(evA - evB))
    fA = _collect_findings_stable(a_dir); fB = _collect_findings_stable(b_dir)
    fi_added = sorted(list(fB - fA))
    fi_removed = sorted(list(fA - fB))
    archA = _collect_arch_items(a_dir); archB = _collect_arch_items(b_dir)
    def list_api_items(obj):
        items = obj.get("items") or []
        return {(x.get("method"), x.get("path")) for x in items}
    api_added = sorted(list(list_api_items(archB.get("api",{})) - list_api_items(archA.get("api",{}))))
    api_removed = sorted(list(list_api_items(archA.get("api",{})) - list_api_items(archB.get("api",{}))))
    # data surface tables/indexes
    def list_names(obj, key):
        return {x.get("name") for x in obj.get(key, [])}
    tables_added = sorted(list(list_names(archB.get("data",{}),"tables") - list_names(archA.get("data",{}),"tables")))
    tables_removed = sorted(list(list_names(archA.get("data",{}),"tables") - list_names(archB.get("data",{}),"tables")))
    indexes_added = sorted(list(list_names(archB.get("data",{}),"indexes") - list_names(archA.get("data",{}),"indexes")))
    indexes_removed = sorted(list(list_names(archA.get("data",{}),"indexes") - list_names(archB.get("data",{}),"indexes")))
    if not tables_added and not tables_removed and not indexes_added and not indexes_removed:
        tbA, ixA = _collect_data_from_db(a_dir)
        tbB, ixB = _collect_data_from_db(b_dir)
        tables_added = sorted(list(tbB - tbA))
        tables_removed = sorted(list(tbA - tbB))
        indexes_added = sorted(list(ixB - ixA))
        indexes_removed = sorted(list(ixA - ixB))
    # deps surface infra changes could be done similarly; keep minimal
    briefA = _collect_brief_eids(a_dir); briefB = _collect_brief_eids(b_dir)
    brief_eids_added = sorted(list(briefB - briefA))
    brief_eids_removed = sorted(list(briefA - briefB))
    # fingerprint warnings
    if fpA.get("mode") == "git" and fpB.get("mode") == "git":
        if fpA.get("head") != fpB.get("head"):
            warnings.append("fingerprint_head_mismatch")
    # compose md
    md = []
    md.append("# Context Diff Report")
    md.append("## Repo Fingerprint Diff")
    md.append(f"- modeA={fpA.get('mode')} modeB={fpB.get('mode')}")
    if "fingerprint_head_mismatch" in warnings:
        md.append("- WARNING: git HEAD differs")
    md.append("## Snapshot Diff")
    md.append(f"- events added: {len(events_added)} removed: {len(events_removed)}")
    for t,k in events_added[:20]: md.append(f"  + {t} {k}")
    for t,k in events_removed[:20]: md.append(f"  - {t} {k}")
    md.append(f"- findings added: {len(fi_added)} removed: {len(fi_removed)}")
    for c,sid in fi_added[:20]: md.append(f"  + {c} {sid}")
    for c,sid in fi_removed[:20]: md.append(f"  - {c} {sid}")
    md.append("## Architecture Views Diff")
    md.append(f"- api_surface added: {len(api_added)} removed: {len(api_removed)}")
    for m,p in api_added[:20]: md.append(f"  + {m} {p}")
    for m,p in api_removed[:20]: md.append(f"  - {m} {p}")
    md.append(f"- data_surface tables added: {len(tables_added)} removed: {len(tables_removed)}")
    for n in tables_added[:20]: md.append(f"  + table {n}")
    for n in tables_removed[:20]: md.append(f"  - table {n}")
    md.append(f"- data_surface indexes added: {len(indexes_added)} removed: {len(indexes_removed)}")
    md.append("## Evidence References Diff")
    md.append(f"- brief evidence ids added: {len(brief_eids_added)} removed: {len(brief_eids_removed)}")
    md.append("## Notes & Uncertainty")
    if warnings:
        md.append(", ".join(warnings))
    else:
        md.append("None")
    (od/"diff_report.md").write_text("\n".join(md), encoding="utf-8")
    diff_json = {
        "fingerprint": {"modeA": fpA.get("mode"), "modeB": fpB.get("mode"), "warnings": warnings},
        "snapshot": {"events": {"added": events_added, "removed": events_removed}, "findings": {"added": fi_added, "removed": fi_removed}},
        "arch": {"api_surface": {"added": api_added, "removed": api_removed}, "data_surface": {"tables": {"added": tables_added, "removed": tables_removed}, "indexes": {"added": indexes_added, "removed": indexes_removed}}},
        "brief": {"evidence_ids": {"added": brief_eids_added, "removed": brief_eids_removed}}
    }
    with open(od/"diff_report.json", "w", encoding="utf-8") as f:
        json.dump(diff_json, f)
    with open(od/"diff_warnings.json", "w", encoding="utf-8") as f:
        json.dump(warnings, f)
    with open(od/"diff_checksums.json", "w", encoding="utf-8") as f:
        json.dump(_sha256_dir(str(od)), f)
    # cleanup
    if a_tmp and Path(a_tmp).exists():
        shutil.rmtree(a_tmp, ignore_errors=True)
    if b_tmp and Path(b_tmp).exists():
        shutil.rmtree(b_tmp, ignore_errors=True)
    if as_json:
        print(json.dumps({"ok": True, "out_dir": str(od)}))
    return str(od)
