import os
import json
import hashlib
from .diff import stable_finding_id
def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}
def _severity_from_conf(conf):
    try:
        c = float(conf or 0.0) * 100
    except Exception:
        c = 0.0
    if c >= 80.0:
        return "error"
    if c >= 50.0:
        return "warning"
    return "note"
def _fingerprint(rule_id, norm_path, start_line, end_line, snippet):
    h = hashlib.sha1()
    h.update(str(rule_id or "").encode("utf-8"))
    h.update(b"|")
    h.update(str(norm_path or "").encode("utf-8"))
    h.update(b"|")
    h.update(str(int(start_line or 0)).encode("utf-8"))
    h.update(b"|")
    h.update(str(int(end_line or 0)).encode("utf-8"))
    if snippet:
        try:
            h.update(b"|")
            h.update(hashlib.sha256(snippet.encode("utf-8")).hexdigest().encode("utf-8"))
        except Exception:
            pass
    return h.hexdigest()
def build_sarif(run_dir):
    report = _read_json(os.path.join(run_dir, "report.json"), {"findings": []})
    findings = report.get("findings", [])
    run_summary = report.get("run_summary") or {}
    manifest = _read_json(os.path.join(run_dir, "manifest.json"), {})
    repo_root = manifest.get("repo_root") or ""
    meta_map = {}
    try:
        import sqlite3
        conn = sqlite3.connect(os.path.join(run_dir, "detections.sqlite"))
        c = conn.cursor()
        rows = c.execute("select fid, meta_json from findings").fetchall()
        for fid, mj in rows:
            try:
                meta_map[int(fid)] = json.loads(mj or "{}")
            except Exception:
                meta_map[int(fid)] = {}
        conn.close()
    except Exception:
        meta_map = {}
    rules = {}
    results = []
    for f in findings:
        mm = meta_map.get(f.get("fid")) or {}
        rid = f.get("rule_id") or f.get("concept") or "rule"
        kind = mm.get("evidence_strength") or ""
        name = f.get("concept") or rid
        rules[rid] = {
            "id": rid,
            "name": name,
            "shortDescription": {"text": f'{name}: {rid}'},
            "fullDescription": {"text": f'Concept {name} detected by rule {rid}'},
            "helpUri": f'docs/rules/{rid}.md',
            "properties": {"concept": name, "kind": kind, "severity": _severity_from_conf(f.get("confidence"))},
        }
        level = _severity_from_conf(f.get("confidence"))
        path = f.get("path", "")
        rel_path = path
        try:
            if repo_root:
                rel_path = os.path.relpath(path, repo_root)
        except Exception:
            pass
        rel_path = (rel_path or "").replace("\\", "/").lstrip("./")
        loc = {
            "physicalLocation": {
                "artifactLocation": {"uri": rel_path},
                "region": {"startLine": int(f.get("start_line") or 0), "endLine": int(f.get("end_line") or 0), "snippet": {"text": f.get("snippet","")}}
            }
        }
        fp = _fingerprint(rid, rel_path, f.get("start_line"), f.get("end_line"), f.get("snippet"))
        props = {"concept": name, "kind": kind, "severity": level}
        for k in ("markers_hit","anti_patterns_hit","score"):
            if k in mm:
                props[k] = mm[k]
        item_for_sid = {
            "concept": f.get("concept"),
            "rule_id": rid,
            "parse_level": f.get("parse_level"),
            "confidence": float(f.get("confidence", 0.0)),
            "primary_eid": f.get("primary_eid"),
            "meta": {"http.method": f.get("api_method"), "http.path": f.get("api_path"), **mm}
        }
        sid, _ = stable_finding_id(item_for_sid)
        results.append({
            "ruleId": rid,
            "level": level,
            "message": {"text": f.get("snippet","")},
            "locations": [loc],
            "fingerprints": {"reposense/v1": fp, "stable_finding_id": sid},
            "properties": props
        })
    runs_props = {
        "reposense.profile": run_summary.get("profile"),
        "reposense.ruleset": run_summary.get("ruleset"),
        "reposense.budget": run_summary.get("budget"),
        "reposense.findings_count": run_summary.get("findings_count"),
        "reposense.events_count": run_summary.get("events_count"),
        "reposense.graph_nodes": run_summary.get("graph_nodes"),
        "reposense.graph_edges": run_summary.get("graph_edges"),
        "reposense.content_id": (run_summary.get("artifacts_missing") or []),
    }
    cov = _read_json(os.path.join(run_dir, "coverage.json"), {})
    cid = (cov.get("content_id") or (cov.get("stats") or {}).get("content_id"))
    pid = (cov.get("pack_id") or (cov.get("stats") or {}).get("pack_id"))
    runs_props["reposense.content_id"] = cid
    runs_props["reposense.pack_id"] = pid
    # gate status
    gate = _read_json(os.path.join(run_dir, "quality_gate.json"), {"status":"N/A","violations":[]})
    runs_props["reposense.gate_status"] = gate.get("status", "N/A")
    sarif = {
        "version": "2.1.0",
        "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "RepoSense",
                    "rules": sorted(list(rules.values()), key=lambda r: r["id"])
                }
            },
            "results": results + ([{
                "ruleId": f"reposense.gate.{v.get('metric')}",
                "level": "error" if v.get("level") == "fail" else "warning",
                "message": {"text": v.get("message","")},
                "locations": []
            } for v in (gate.get("violations") or [])] if gate.get("status") in ("fail","warn") else []),
            "properties": runs_props
        }]
    }
    return sarif
def export_sarif(run_dir, out_path):
    sarif = build_sarif(run_dir)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(sarif, f, ensure_ascii=False)
def run_export_sarif(run_dir, out_path):
    export_sarif(run_dir, out_path)
    print(out_path)
