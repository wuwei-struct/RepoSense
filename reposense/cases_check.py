import os
import json
from pathlib import Path
def _validate_with_schema(doc, schema_path, strict=False):
    try:
        import jsonschema
    except ImportError:
        if strict:
            return False, ["jsonschema_missing"], []
        else:
            return True, [], ["jsonschema_missing"]
    schema = json.load(open(schema_path, "r", encoding="utf-8"))
    try:
        import jsonschema
        jsonschema.validate(doc, schema)
        return True, [], []
    except Exception as e:
        return False, [str(e)], []
def cases_check(path, as_json=False, strict_schema=False):
    p = Path(path)
    errors = []
    warnings = []
    schema = Path(__file__).resolve().parents[1]/"specs"/"schemas"/"case.schema.json"
    schema_validation = "performed"
    if not schema.exists():
        schema_validation = "skipped_missing_schema"
    for fp in sorted(p.rglob("*.case.json")):
        try:
            data = json.load(open(fp, "r", encoding="utf-8"))
        except:
            errors.append(f"parse_failed:{fp.name}")
            continue
        if schema.exists():
            ok, es, ws = _validate_with_schema(data, schema, strict=strict_schema)
            errors.extend(es)
            warnings.extend(ws)
            if "skipped_missing_dependency" in ws:
                schema_validation = "skipped_missing_dependency"
        if not data.get("concept_id"):
            errors.append(f"missing_concept_id:{fp.name}")
        if not data.get("evidence_refs"):
            errors.append(f"missing_evidence:{fp.name}")
        # curated must have teach fields when directory name contains 'curated'
        if "curated" in str(fp):
            if not data.get("title") or not data.get("teach") or not data.get("questions"):
                errors.append(f"curated_missing_teach:{fp.name}")
    ok = len(errors)==0
    warnings = sorted(warnings + [schema_validation])
    out = {"ok": ok, "errors": errors, "warnings": warnings, "schema_validation": schema_validation}
    if as_json:
        print(json.dumps(out))
    else:
        print(f"ok={ok} errors={len(errors)} warnings={len(warnings)}")
    return ok
