from .run_reader import open_run
from .difficulty import compute_difficulty
def extract_cases(run_dir):
    rh = open_run(run_dir)
    cases = []
    for f in rh.iter_findings():
        evid = rh.get_finding_evidence(f["fid"])
        parse_levels = [e["parse_level"] for e in evid]
        diff = compute_difficulty(evid, parse_levels, f.get("meta") or {})
        cases.append({
            "concept": (f.get("concept") or "").lower(),
            "difficulty": diff,
            "fid": f["fid"],
            "rule_id": f.get("rule_id"),
            "confidence": f["confidence"],
            "primary_eid": f["primary_eid"],
            "evidence_refs": evid,
            "notes": {"meta_echo": f.get("meta") or {}}
        })
    rh.close()
    return cases
