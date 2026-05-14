def compute_difficulty(evidence_refs, parse_levels, meta):
    if not evidence_refs:
        return 1
    same_file = len(set([e["path"] for e in evidence_refs])) == 1
    has_l3 = any(pl == "L3" for pl in parse_levels)
    if len(evidence_refs) == 1 and same_file and not has_l3:
        return 1
    if has_l3 or len(evidence_refs) > 1 or not same_file:
        # check if meta marks explicit chain
        flags = set()
        for k in ["multi_concept","chain","pipeline"]:
            v = meta.get(k)
            if v:
                flags.add(k)
        return 3 if flags else 2
    return 2
