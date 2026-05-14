import os
import json
import time
from .versioning import ruleset_fingerprint, generated_by
def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}
def _sev_rank(s):
    return {"error": 3, "warning": 2, "note": 1}.get((s or "note").lower(), 0)
def save_baseline(run_dir, out_path, profile="prod_lite", ruleset="rulesets/specs_v2", gate_id="prod_lite"):
    sarif = _read_json(os.path.join(run_dir, "exports", "report.sarif.json"), {"runs": []})
    runs = sarif.get("runs") or []
    findings = []
    if runs:
        res = runs[0].get("results") or []
        for r in res:
            fp = (r.get("fingerprints") or {}).get("reposense/v1") or (r.get("fingerprints") or {}).get("stable_finding_id")
            lvl = r.get("level") or (r.get("properties") or {}).get("severity")
            locs = r.get("locations") or []
            if not locs:
                continue
            reg = locs[0].get("physicalLocation", {}).get("region", {}) or {}
            art = locs[0].get("physicalLocation", {}).get("artifactLocation", {}) or {}
            findings.append({
                "fp": fp or "",
                "severity": (lvl or "note"),
                "ruleId": r.get("ruleId"),
                "concept": ((r.get("properties") or {}).get("concept") or ""),
                "path": (art.get("uri") or ""),
                "startLine": int(reg.get("startLine") or 0),
                "endLine": int(reg.get("endLine") or 0),
            })
    # stable order
    findings.sort(key=lambda x: (-_sev_rank(x["severity"]), x.get("concept",""), x.get("ruleId",""), x.get("path",""), x.get("startLine",0), x.get("fp","")))
    cov = _read_json(os.path.join(run_dir, "coverage.json"), {})
    content_id = (cov.get("content_id") or (cov.get("stats") or {}).get("content_id"))
    pack_id = (cov.get("pack_id") or (cov.get("stats") or {}).get("pack_id"))
    fp = ruleset_fingerprint(ruleset) if os.path.isdir(ruleset) else ""
    out = {
        "schema_version": 1,
        "created_at": 0,
        "profile": profile,
        "ruleset": ruleset,
        "ruleset_fingerprint": fp,
        "gate_id": gate_id,
        "source": {"content_id": content_id, "pack_id": pack_id},
        "findings": findings,
        "generated_by": generated_by("0.1.0", os.path.basename(ruleset), fp, 1)
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    return out
def compute_diff(base_path, new_run_dir, out_json_path, out_md_path=None, current_ruleset_dir="rulesets/specs_v2"):
    base = _read_json(base_path, {"findings": []})
    sarif = _read_json(os.path.join(new_run_dir, "exports", "report.sarif.json"), {"runs": []})
    runs = sarif.get("runs") or []
    new_findings = []
    if runs:
        res = runs[0].get("results") or []
        for r in res:
            fp = (r.get("fingerprints") or {}).get("reposense/v1") or (r.get("fingerprints") or {}).get("stable_finding_id")
            lvl = r.get("level") or (r.get("properties") or {}).get("severity")
            locs = r.get("locations") or []
            if not locs:
                continue
            reg = locs[0].get("physicalLocation", {}).get("region", {}) or {}
            art = locs[0].get("physicalLocation", {}).get("artifactLocation", {}) or {}
            new_findings.append({
                "fp": fp or "",
                "severity": (lvl or "note"),
                "ruleId": r.get("ruleId"),
                "concept": ((r.get("properties") or {}).get("concept") or ""),
                "path": (art.get("uri") or ""),
                "startLine": int(reg.get("startLine") or 0),
                "endLine": int(reg.get("endLine") or 0),
            })
    # index by fp
    base_idx = {f.get("fp") or "": f for f in (base.get("findings") or [])}
    new_idx = {f.get("fp") or "": f for f in new_findings}
    added = []
    removed = []
    changed = []
    for fp, nf in new_idx.items():
        bf = base_idx.get(fp)
        if not bf:
            added.append(nf)
        else:
            if (bf.get("severity") or "note") != (nf.get("severity") or "note"):
                changed.append({"fp": fp, "from": bf.get("severity"), "to": nf.get("severity"), **nf})
    for fp, bf in base_idx.items():
        if fp not in new_idx:
            removed.append(bf)
    def _st_key(x):
        return (-_sev_rank(x.get("severity")), x.get("concept",""), x.get("ruleId",""), x.get("path",""), int(x.get("startLine") or 0), x.get("fp",""))
    added.sort(key=_st_key)
    removed.sort(key=_st_key)
    changed.sort(key=lambda x: (-_sev_rank(x.get("to")), x.get("concept",""), x.get("ruleId",""), x.get("path",""), int(x.get("startLine") or 0), x.get("fp","")))
    stats = {
        "added_error": len([a for a in added if (a.get("severity") or "").lower() == "error"]),
        "added_warning": len([a for a in added if (a.get("severity") or "").lower() == "warning"]),
        "severity_upgrades": len([c for c in changed if _sev_rank(c.get("to")) > _sev_rank(c.get("from"))]),
        "removed": len(removed),
    }
    cur_fp = ruleset_fingerprint(current_ruleset_dir) if os.path.isdir(current_ruleset_dir) else ""
    base_fp = base.get("ruleset_fingerprint") or ""
    if not base_fp:
        compatible = True
    else:
        compatible = bool(cur_fp) and (cur_fp == base_fp)
    out = {
        "schema_version": 1,
        "base_meta": {"count": len(base.get("findings") or [])},
        "new_meta": {"count": len(new_findings), "ruleset_fingerprint": cur_fp},
        "stats": stats,
        "added": added,
        "removed": removed,
        "severity_changed": changed,
        "compatible": compatible,
        "generated_by": generated_by("0.1.0", os.path.basename(current_ruleset_dir), cur_fp, 1)
    }
    os.makedirs(os.path.dirname(out_json_path), exist_ok=True)
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    if out_md_path:
        try:
            lines = []
            lines.append("# Diff Summary")
            lines.append(f"- added_error: {stats['added_error']}")
            lines.append(f"- added_warning: {stats['added_warning']}")
            lines.append(f"- severity_upgrades: {stats['severity_upgrades']}")
            lines.append(f"- removed: {stats['removed']}")
            with open(out_md_path, "w", encoding="utf-8") as f2:
                f2.write("\n".join(lines))
        except Exception:
            pass
    return out
