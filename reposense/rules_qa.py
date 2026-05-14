import os
import json
import re
import yaml
from .rules import load_ruleset
from .scanner import walk_files, collect_file_info
from .detectors import run_detectors
def rules_check(ruleset_dir):
    p = os.path.join(ruleset_dir, "rules.yaml")
    data = yaml.safe_load(open(p, "r", encoding="utf-8"))
    seen = set()
    errors = []
    warnings = []
    kinds = {"text","openapi","gha","dockerfile","compose","sql_ddl","sql_tx","deps","ast","python_ast"}
    for r in data:
        rid = r.get("rule_id")
        if not rid:
            errors.append("missing rule_id")
        elif rid in seen:
            errors.append(f"duplicate rule_id {rid}")
        else:
            seen.add(rid)
        globs = r.get("globs", [])
        for g in globs:
            if not isinstance(g, str):
                errors.append(f"invalid glob in {rid}")
        pats = r.get("patterns", [])
        for ptn in pats or []:
            if ptn.get("type") == "regex":
                try:
                    re.compile(ptn["value"])
                except Exception:
                    errors.append(f"invalid regex in {rid}")
        kind = r.get("kind")
        if kind not in kinds:
            errors.append(f"unknown kind {kind} in {rid}")
        if kind == "ast" and not r.get("matcher"):
            errors.append(f"ast matcher missing in {rid}")
    return {"ok": len(errors)==0, "errors": errors, "warnings": warnings}
def rules_coverage(ruleset_dir, fixtures_dir):
    ruleset = load_ruleset(ruleset_dir)
    concepts = set([r.get("concept") for r in ruleset["rules"] if r.get("concept")])
    hits = {c:0 for c in concepts}
    # collect files under fixtures_dir
    files = []
    for root, dirs, fnames in os.walk(fixtures_dir):
        for nm in fnames:
            files.append({"path": os.path.join(root, nm)})
    budget = {"max_files": 10000, "max_file_size": 1024*1024}
    results, _ = run_detectors(ruleset, files, budget)
    for r in results:
        c = r.get("concept")
        if c in hits:
            hits[c] += 1
    uncovered = sorted([c for c in hits if hits[c] == 0])
    return {"ok": len(uncovered)==0, "hits": hits, "uncovered": uncovered}
def run_rules_check(ruleset_dir, as_json):
    res = rules_check(ruleset_dir)
    print(json.dumps(res) if as_json else f'ok={res["ok"]} errors={len(res["errors"])}')
def run_rules_coverage(ruleset_dir, fixtures_dir, as_json):
    res = rules_coverage(ruleset_dir, fixtures_dir)
    print(json.dumps(res) if as_json else f'ok={res["ok"]} uncovered={len(res["uncovered"])}')
