import os
import json
import hashlib
import glob
def _sha256(path):
    try:
        with open(path, "rb") as f:
            h = hashlib.sha256()
            while True:
                b = f.read(8192)
                if not b: break
                h.update(b)
            return h.hexdigest()
    except Exception:
        return None
def _artifact_kind(rel):
    if rel == "report.json": return "report"
    if rel == "event_graph.json": return "event_graph"
    if rel == "api_surface.json": return "api_surface"
    if rel == "entrypoints.json": return "entrypoints"
    if rel == "coverage.json": return "coverage"
    if rel == "ci_summary.json": return "ci_summary"
    if rel == "quality_gate.json": return "quality_gate"
    if rel == "patterns.json": return "patterns"
    if rel == "pattern_summary.json": return "pattern_summary"
    if rel == "ai_summary.json": return "ai_summary"
    if rel == "ai_summary.md": return "ai_summary"
    if rel.endswith("/snippet_pack.json") and rel.startswith("ai_drilldown/"): return "ai_drilldown"
    if rel.endswith("/snippet_pack.md") and rel.startswith("ai_drilldown/"): return "ai_drilldown"
    if rel.endswith("/explain.json") and rel.startswith("ai_explain/"): return "ai_explain"
    if rel.endswith("/explain.md") and rel.startswith("ai_explain/"): return "ai_explain"
    if rel == "ai_risks/risks.json": return "ai_risks"
    if rel == "ai_risks/risks.md": return "ai_risks"
    if rel == "backend_verifier_report.json": return "backend_verifier_report"
    if rel == "backend_verifier_report.md": return "backend_verifier_report"
    if rel.endswith("/answer.json") and rel.startswith("ai_ask/"): return "ai_ask"
    if rel.endswith("/answer.md") and rel.startswith("ai_ask/"): return "ai_ask"
    if rel.startswith("exports/"): return "exports"
    if rel.startswith("context_pack/"): return "context_pack"
    return "other"
def build_run_manifest(run_dir, write=True):
    artifacts = []
    rels = ["report.json","event_graph.json","api_surface.json","entrypoints.json","coverage.json","ci_summary.json","quality_gate.json","api_callers.json","cross_language_links.json","cross_language_summary.json","api_topology.json","patterns.json","pattern_summary.json","ai_summary.json","ai_summary.md","ai_risks/risks.json","ai_risks/risks.md","backend_verifier_report.json","backend_verifier_report.md","baseline_in.json","baseline_diff.json","baseline_diff.md","exports/report.sarif.json","context_pack/ARTIFACTS/run_summary.json","context_pack/ARTIFACTS/quality_gate.json","context_pack/ARTIFACTS/baseline_diff.json","context_pack/ARTIFACTS/baseline_in.json","context_pack/ARTIFACTS/run_manifest.json","context_pack/ARTIFACTS/api_callers.json","context_pack/ARTIFACTS/cross_language_summary.json","context_pack/ARTIFACTS/patterns.json","context_pack/ARTIFACTS/pattern_summary.json","context_pack/ARTIFACTS/ai_summary.json","context_pack/ARTIFACTS/ai_summary.md","context_pack/MAP/cross_language_links.json","context_pack/MAP/api_topology.json"]
    for p in sorted(glob.glob(os.path.join(run_dir, "ai_drilldown", "*", "snippet_pack.json"))):
        rels.append(os.path.relpath(p, run_dir).replace("\\", "/"))
    for p in sorted(glob.glob(os.path.join(run_dir, "ai_drilldown", "*", "snippet_pack.md"))):
        rels.append(os.path.relpath(p, run_dir).replace("\\", "/"))
    for p in sorted(glob.glob(os.path.join(run_dir, "ai_explain", "*", "explain.json"))):
        rels.append(os.path.relpath(p, run_dir).replace("\\", "/"))
    for p in sorted(glob.glob(os.path.join(run_dir, "ai_explain", "*", "explain.md"))):
        rels.append(os.path.relpath(p, run_dir).replace("\\", "/"))
    for p in sorted(glob.glob(os.path.join(run_dir, "ai_ask", "*", "answer.json"))):
        rels.append(os.path.relpath(p, run_dir).replace("\\", "/"))
    for p in sorted(glob.glob(os.path.join(run_dir, "ai_ask", "*", "answer.md"))):
        rels.append(os.path.relpath(p, run_dir).replace("\\", "/"))
    for rel in rels:
        p = os.path.join(run_dir, rel)
        if os.path.isfile(p):
            sha = _sha256(p)
            artifacts.append({
                "path": rel,
                "kind": _artifact_kind(rel),
                "schema_version": None,
                "bytes": os.path.getsize(p),
                "sha256": sha,
                "generated_by": None
            })
    # stable sorting
    artifacts.sort(key=lambda x: (x["kind"], x["path"]))
    meta = {"run_dir": run_dir}
    try:
        with open(os.path.join(run_dir, "coverage.json"), "r", encoding="utf-8") as f:
            cov = json.load(f)
        meta["content_id"] = cov.get("content_id")
        meta["pack_id"] = cov.get("pack_id")
    except Exception:
        pass
    try:
        with open(os.path.join(run_dir, "report.json"), "r", encoding="utf-8") as f:
            rep = json.load(f)
        rsid = ((rep.get("generated_by") or {}).get("ruleset_id")) or None
        rsfp = ((rep.get("generated_by") or {}).get("ruleset_fingerprint")) or None
        meta["profile"] = (rep.get("run_summary") or {}).get("profile")
        meta["ruleset_id"] = rsid
        meta["ruleset_fingerprint"] = rsfp
    except Exception:
        pass
    gb = None
    try:
        with open(os.path.join(run_dir, "quality_gate.json"), "r", encoding="utf-8") as f:
            gb = json.load(f).get("generated_by")
    except Exception:
        try:
            with open(os.path.join(run_dir, "report.json"), "r", encoding="utf-8") as f:
                gb = json.load(f).get("generated_by")
        except Exception:
            gb = None
    out = {"schema_version": 1, "meta": meta, "artifacts": artifacts, "generated_by": gb}
    if write:
        with open(os.path.join(run_dir, "run_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False)
    return out
