def validate_case(case, concept_ids=None):
    req = ["case_id", "concept_id", "level", "title", "repo_ref", "evidence_refs", "explain", "what", "why", "how", "risk", "labels", "metadata"]
    errs = []
    for k in req:
        if k not in case:
            errs.append(f"missing:{k}")
    lvl = int(case.get("level") or 0)
    if lvl not in (1, 2, 3):
        errs.append("invalid:level")
    if concept_ids is not None and str(case.get("concept_id") or "").lower() not in set([str(x).lower() for x in concept_ids]):
        errs.append("invalid:concept_id")
    if not isinstance(case.get("evidence_refs") or [], list) or len(case.get("evidence_refs") or []) == 0:
        errs.append("invalid:evidence_refs")
    return {"ok": len(errs) == 0, "errors": errs}
