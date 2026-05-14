import json
from collections import deque, defaultdict
from .concept_graph import ConceptGraph, load_concept_graph
from .case_extractor import extract_cases
def toposort(graph, start_id, max_depth=4):
    # BFS collecting prerequisites
    cg = ConceptGraph(graph)
    # map id->info
    id_to_info = { (c.get("concept_id") or c["concept"]).lower(): c for c in graph.get("concepts", [])}
    start = start_id.lower()
    order = []
    visited = set()
    q = deque([start])
    depth = {start: 0}
    while q:
        cur = q.popleft()
        if cur in visited: continue
        visited.add(cur)
        order.append(cur)
        info = id_to_info.get(cur)
        if not info: continue
        for pre in (info.get("prerequisites") or []):
            pre_l = pre.lower()
            if pre_l not in visited and depth[cur] + 1 <= max_depth:
                depth[pre_l] = depth[cur] + 1
                q.append(pre_l)
    # reverse to ensure prerequisites come first
    order = list(reversed(order))
    return order
def pick_cases_for_concepts(concepts, graph, run_dir=None, lib_dir=None, max_per=3):
    res = defaultdict(list)
    cg = ConceptGraph(graph)
    # source cases
    cases = []
    if lib_dir:
        import os
        from pathlib import Path
        cb = Path(lib_dir).resolve() / "casebank.jsonl"
        if cb.exists():
            for ln in cb.read_text(encoding="utf-8").splitlines():
                try:
                    item = json.loads(ln)
                    best = item.get("sources", [])[0] if item.get("sources") else {}
                    cases.append({
                        "concept": cg.get(item["concept_id"])["concept"].lower(),
                        "difficulty": item.get("level", 1),
                        "confidence": item.get("confidence", 0.0),
                        "evidence_refs": best.get("evidence_refs") or []
                    })
                except:
                    pass
    elif run_dir:
        cases = extract_cases(run_dir)
    # selection rule: L3 > L2 > L1, then confidence desc
    def score(c):
        lvl = 1
        if c["evidence_refs"]:
            pl = c["evidence_refs"][0].get("parse_level","L1")
            lvl = {"L1":1,"L2":2,"L3":3}.get(pl,1)
        return (lvl, float(c.get("confidence",0.0)))
    for cid in concepts:
        name = cg.get(cid)["concept"].lower() if cg.get(cid) else cid
        pool = [c for c in cases if c["concept"] == name]
        pool.sort(key=score, reverse=True)
        res[cid] = pool[:max_per]
    return res
