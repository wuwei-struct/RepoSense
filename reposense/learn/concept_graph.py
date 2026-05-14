import os
import json
from pathlib import Path


def default_concept_graph_path():
    return str(Path(__file__).resolve().parent.parent / "shared" / "concepts" / "concepts.json")


def load_concept_graph(path):
    p = path or default_concept_graph_path()
    if not os.path.isfile(p):
        p = path
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
def load_concept_map(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
def check_graph_and_map(graph, cmap):
    errors = []
    warnings = []
    cg = ConceptGraph(graph)
    ids = set([str(c.get("concept_id") or c.get("concept") or c.get("name") or c.get("title") or "").lower() for c in graph.get("concepts", []) if (c.get("concept_id") or c.get("concept") or c.get("name") or c.get("title"))])
    m = cmap.get("map", {})
    # each mapped concept points to existing concept_id
    for k, v in m.items():
        if str(v).lower() not in ids:
            errors.append(f"map target missing: {k}->{v}")
    # duplicates
    targets = [str(v).lower() for v in m.values()]
    if len(set(targets)) != len(targets):
        errors.append("duplicate concept_id in map")
    return {"ok": len(errors)==0, "errors": errors, "warnings": warnings}
def validate_concept_graph(graph):
    errors = []
    warnings = []
    seen = set()
    items = graph.get("concepts", [])
    ids = [c.get("concept_id") or c.get("concept") or c.get("name") or c.get("title") for c in items]
    id_set = set([str(x).lower() for x in ids if x])
    for c in items:
        name = c.get("concept") or c.get("name") or c.get("title")
        if not name:
            errors.append("missing concept name")
            continue
        cid = c.get("concept_id") or name
        cid_l = str(cid).lower()
        if cid_l in seen:
            errors.append(f"duplicate concept_id {cid}")
        seen.add(cid_l)
        if not c.get("category"):
            errors.append(f"category missing for {name}")
        for ref in (c.get("prerequisites") or []):
            if str(ref).lower() not in id_set:
                errors.append(f"prerequisite {ref} missing for {cid}")
        for ref in (c.get("related") or []):
            if str(ref).lower() not in id_set:
                errors.append(f"related {ref} missing for {cid}")
    return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings}
class ConceptGraph:
    def __init__(self, graph):
        self.graph = graph
        self._by_name = {}
        self._by_lower = {}
        self._by_id = {}
        for c in graph.get("concepts", []):
            nm = c.get("concept") or c.get("name") or c.get("title") or c.get("concept_id")
            cid = c.get("concept_id") or nm
            if nm:
                self._by_name[nm] = c
                self._by_lower[str(nm).lower()] = c
            if cid:
                self._by_id[str(cid).lower()] = c
    def get(self, concept):
        key = str(concept).lower()
        got = self._by_name.get(concept) or self._by_lower.get(key) or self._by_id.get(key)
        if got:
            return got
        alias = {
            "infra.queue": "async.queue",
            "infra.scheduler": "async.scheduler",
            "infra.workflow": "async.workflow",
        }
        ak = alias.get(key)
        if ak:
            return self._by_id.get(ak) or self._by_lower.get(ak)
        return None
    def all_concepts(self):
        return [c.get("concept") or c.get("name") or c.get("title") or c.get("concept_id") for c in self.graph.get("concepts", [])]
    def by_category(self):
        res = {}
        for c in self.graph.get("concepts", []):
            cat = c.get("category") or "uncategorized"
            res.setdefault(cat, []).append(c["concept"])
        return res
