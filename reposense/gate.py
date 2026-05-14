import os
import json
import sqlite3
from .diff import stable_finding_id
def load_policy(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
def read_manifest(run_dir):
    with open(os.path.join(run_dir, "manifest.json"), "r", encoding="utf-8") as f:
        return json.load(f)
def load_allowlist(repo_root):
    p = os.path.join(repo_root, ".reposense", "allowlist.json")
    if not os.path.exists(p):
        return {"findings": []}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"findings": []}
def collect_findings(run_dir):
    conn = sqlite3.connect(os.path.join(run_dir, "detections.sqlite"))
    c = conn.cursor()
    rows = c.execute("select f.fid, f.concept, f.rule_id, e.parse_level, f.confidence, f.primary_eid, f.meta_json from findings f join evidence e on e.eid=f.primary_eid").fetchall()
    try:
        conn.close()
    except:
        pass
    items = []
    for fid, concept, rule_id, parse_level, confidence, primary_eid, meta_json in rows:
        m = {}
        try:
            m = json.loads(meta_json or "{}")
        except:
            m = {}
        items.append({"fid": fid, "concept": concept, "rule_id": rule_id, "parse_level": parse_level, "confidence": float(confidence), "primary_eid": primary_eid, "meta": m})
    return items
def run_gate_policy(run_dir, policy_path, as_json):
    policy = load_policy(policy_path)
    manifest = read_manifest(run_dir)
    repo_root = manifest.get("repo_root","")
    allow = load_allowlist(repo_root)
    allow_ids = set(allow.get("findings", []))
    items = collect_findings(run_dir)
    min_level = policy.get("min_parse_level","L2")
    min_conf = float(policy.get("min_confidence", 0.0))
    thresholds = policy.get("thresholds", {})
    fail_on = policy.get("fail_on")
    counts = {}
    violations = {}
    ignored = 0
    for it in items:
        if it["parse_level"] not in ("L2","L3") and min_level in ("L2","L3"):
            continue
        if it["confidence"] < min_conf:
            continue
        sid, ok = stable_finding_id(it)
        if sid in allow_ids:
            ignored += 1
            continue
        concept = it["concept"]
        if fail_on and concept not in fail_on:
            continue
        counts[concept] = counts.get(concept, 0) + 1
        if counts[concept] > thresholds.get(concept, 999999):
            violations.setdefault(concept, []).append({"stable_id": sid, "fid": it["fid"], "parse_level": it["parse_level"], "confidence": it["confidence"]})
    ok = len(violations) == 0
    res = {
        "ok": ok,
        "violations": violations,
        "ignored_by_allowlist": ignored,
        "policy_hash": ""  # 可选：后续加入
    }
    if as_json:
        print(json.dumps(res))
    else:
        lines = []
        lines.append(f"ok={ok}")
        if violations:
            lines.append("violations:")
            for k, v in violations.items():
                lines.append(f"- {k}: {len(v)}")
        lines.append(f"ignored_by_allowlist={ignored}")
        print("\n".join(lines))
    return ok
