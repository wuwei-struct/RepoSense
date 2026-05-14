import os
import json
import yaml
from pathlib import Path
def _validate_with_schema(doc, schema_path, strict=False):
    try:
        import jsonschema
    except ImportError:
        status = "skipped_missing_dependency"
        if strict:
            return False, ["jsonschema_missing"], [status]
        else:
            return True, [], [status]
    schema = json.load(open(schema_path, "r", encoding="utf-8"))
    try:
        jsonschema.validate(doc, schema)
        return True, [], ["performed"]
    except Exception as e:
        msg = str(e)
        return False, [msg], ["performed"]
def load_from_specs(specs_dir):
    sd = Path(specs_dir)
    concepts = []
    for fp in sorted((sd/"concepts").glob("*.yaml")):
        data = yaml.safe_load(fp.read_text(encoding="utf-8"))
        cid = data.get("id")
        cname = data.get("concept") or (cid.split(".")[-1] if cid else "")
        concepts.append({
            "concept_id": data.get("id"),
            "concept": cname,
            "title": data.get("title", cname),
            "short_definition": data.get("summary", ""),
            "category": data.get("category"),
            "prerequisites": (data.get("relationships") or {}).get("prerequisites") or [],
            "related": (data.get("relationships") or {}).get("related") or []
        })
    return {"version":"1.1-specs","concepts": concepts}
def export_graph_json(specs_dir, out_path):
    graph = load_from_specs(specs_dir)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(graph, f)
def check_specs(specs_dir, strict_schema=False):
    sd = Path(specs_dir)
    errors = []
    warnings = []
    schema_validation = "performed"
    # concept schema path
    c_schema = sd/"schemas"/"concept.schema.json"
    if not c_schema.exists():
        schema_validation = "skipped_missing_schema"
        if strict_schema:
            errors.append("schema_missing:concept")
        else:
            warnings.append("schema_missing:concept")
    # categories
    cats = []
    cfp = sd/"taxonomies"/"categories.yaml"
    if cfp.exists():
        catdoc = yaml.safe_load(cfp.read_text(encoding="utf-8")) or {}
        raw = catdoc.get("categories") or []
        if raw and isinstance(raw[0], dict):
            cats = [c.get("id") for c in raw if c.get("id")]
        else:
            cats = raw
    # concepts
    items = []
    ids = set()
    for fp in sorted((sd/"concepts").glob("*.yaml")):
        data = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
        if c_schema.exists():
            ok, es, ws = _validate_with_schema(data, c_schema, strict=strict_schema)
            errors.extend(es)
            warnings.extend(ws)
            if "skipped_missing_dependency" in ws:
                schema_validation = "skipped_missing_dependency"
        cid = (data.get("id") or "").lower()
        if not cid:
            errors.append("missing id in " + fp.name)
            continue
        if cid in ids:
            errors.append(f"duplicate id {cid}")
        ids.add(cid)
        cat = data.get("category")
        if cats and cat not in cats:
            errors.append(f"bad category {cat} in {fp.name}")
        rel = (data.get("relationships") or {})
        for ref in (rel.get("prerequisites") or []):
            if (ref or "").lower() not in ids and not any((sd/"concepts"/f"{ref}.yaml").exists() for ref in [ref]):
                # since we load sequentially, do final pass later
                pass
        items.append(data)
    # final cross ref
    idset = set([(d.get("id") or "").lower() for d in items if d.get("id")])
    for d in items:
        rel = (d.get("relationships") or {})
        for ref in (rel.get("prerequisites") or []):
            if (ref or "").lower() not in idset:
                errors.append(f"bad prerequisite {ref} in {d.get('id')}")
        for ref in (rel.get("related") or []):
            if (ref or "").lower() not in idset:
                errors.append(f"bad related {ref} in {d.get('id')}")
    errors = sorted(errors)
    warnings = sorted(warnings + ([schema_validation] if schema_validation else []))
    return {"ok": len(errors)==0, "errors": errors, "warnings": warnings, "schema_validation": schema_validation}
def compile_rulesets(specs_dir, out_dir):
    sd = Path(specs_dir)
    od = Path(out_dir).resolve()
    od.mkdir(parents=True, exist_ok=True)
    r_schema = sd/"schemas"/"ruleset.schema.json"
    rules = []
    for fp in sorted((sd/"rulesets").glob("*.yaml")):
        spec = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
        if r_schema.exists():
            _validate_with_schema(spec, r_schema, strict=False)
        rid_base = Path(fp).stem
        concept_name = spec.get("concept") or rid_base
        det = spec.get("detector")
        kind = None
        if isinstance(det, dict):
            kind = det.get("kind")
        elif isinstance(det, str):
            kind = det
        signals = (spec.get("signals") or {})
        any_of = signals.get("any_of") or {}
        # defaults per kind
        kind_globs = {
            "text": ["**/*"],
            "openapi": ["**/*.yaml", "**/*.yml", "**/*.json"],
            "compose": ["**/docker-compose.yml","**/compose.yaml","**/docker-compose.yaml"],
            "sql_ddl": ["**/*.sql"],
            "gha": ["**/.github/workflows/*.yml","**/.github/workflows/*.yaml"],
            "python_ast": ["**/*.py"],
            "sql_tx": ["**/*.sql"],
        }
        if kind == "text" or (not kind and (any_of.get("keywords") or any_of.get("patterns"))):
            kws = any_of.get("keywords") or []
            pats = any_of.get("patterns") or []
            patterns = []
            for kw in kws:
                word = str(kw)
                patterns.append({"regex":rf"\b{word}\b"})
            for pat in pats:
                patterns.append({"regex":str(pat)})
            meta = {}
            gating = spec.get("gating")
            if gating:
                meta["gating"] = {
                    "required_markers_all": gating.get("required_markers_all") or [],
                    "anti_patterns_block_if": gating.get("anti_patterns_block_if") or []
                }
            scoring = spec.get("scoring")
            if scoring:
                meta["scoring"] = {
                    "weight_strong": float(scoring.get("weight_strong", 0.5)),
                    "weight_medium": float(scoring.get("weight_medium", 0.35)),
                    "penalty_negative": float(scoring.get("penalty_negative", 0.3))
                }
            sig_groups = {}
            if signals.get("strong"):
                sig_groups["strong"] = list(signals.get("strong") or [])
            if signals.get("medium"):
                sig_groups["medium"] = list(signals.get("medium") or [])
            if signals.get("negative"):
                sig_groups["negative"] = list(signals.get("negative") or [])
            if sig_groups:
                meta["signals"] = sig_groups
            if patterns or meta:
                rules.append({
                    "rule_id": rid_base+"_text",
                    "rule_version": 1,
                    "concept": concept_name,
                    "kind": "text",
                    "parse_level": "L1",
                    "confidence_base": 0.35,
                    "globs": kind_globs["text"],
                    "snippet": 8,
                    "patterns": patterns,
                    "meta": meta
                })
        if kind == "python_ast":
            matcher = None
            conf = None
            parse_level = "L3"
            snippet = 6
            if isinstance(det, dict):
                matcher = det.get("matcher")
                conf = det.get("confidence")
                parse_level = det.get("parse_level", parse_level)
                snippet = int(det.get("snippet", snippet))
            if matcher:
                rules.append({
                    "rule_id": rid_base+"_python_ast",
                    "rule_version": 1,
                    "concept": concept_name,
                    "kind": "python_ast",
                    "matcher": matcher,
                    "parse_level": parse_level,
                    "confidence_base": 0.7,
                    "confidence": float(conf) if conf is not None else 0.86,
                    "globs": kind_globs["python_ast"],
                    "snippet": snippet
                })
        if kind == "sql_tx":
            rules.append({
                "rule_id": rid_base+"_sql_tx",
                "rule_version": 1,
                "concept": concept_name,
                "kind": "sql_tx",
                "parse_level": "L2",
                "confidence_base": 0.6,
                "globs": kind_globs["sql_tx"],
                "snippet": 5
            })
        for k in ["openapi","compose","sql_ddl","gha"]:
            if kind == k:
                rules.append({
                    "rule_id": rid_base+"_"+k,
                    "rule_version": 1,
                    "concept": concept_name,
                    "kind": k,
                    "parse_level": "L2",
                    "confidence_base": 0.6,
                    "globs": kind_globs[k],
                    "snippet": 5
                })
    # write rules.yaml and version
    (od/"rules.yaml").write_text(yaml.safe_dump(rules, sort_keys=False, allow_unicode=True), encoding="utf-8")
    with open(od/"ruleset_version.json","w",encoding="utf-8") as f:
        json.dump({"version":"specs_v1"}, f)
def fingerprint_specs(specs_dir):
    base = Path(specs_dir).resolve()
    files = []
    for root, dirs, fs in os.walk(base):
        for nm in sorted(fs):
            p = Path(root)/nm
            rel = str(p.relative_to(base)).replace("\\","/")
            files.append(rel)
    import hashlib
    h = hashlib.sha256()
    for rel in sorted(files):
        with open(str(base/rel), "rb") as f:
            h.update(f.read())
    return {"specs_dir": str(base), "sha256": h.hexdigest()}
