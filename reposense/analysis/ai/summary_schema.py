import json


def normalize_summary(obj):
    s = dict(obj or {})
    s["version"] = str(s.get("version") or "ai-summary-v1")
    s["run_dir"] = str(s.get("run_dir") or "")
    s["generated_at"] = str(s.get("generated_at") or "")
    s["mode"] = "facts_only"
    s["project_overview"] = s.get("project_overview") if isinstance(s.get("project_overview"), dict) else {}
    s["stack_summary"] = s.get("stack_summary") if isinstance(s.get("stack_summary"), dict) else {}
    s["surface_summary"] = s.get("surface_summary") if isinstance(s.get("surface_summary"), dict) else {}
    s["flow_summary"] = s.get("flow_summary") if isinstance(s.get("flow_summary"), dict) else {}
    s["risk_summary"] = s.get("risk_summary") if isinstance(s.get("risk_summary"), dict) else {}
    s["priority_actions"] = s.get("priority_actions") if isinstance(s.get("priority_actions"), list) else []
    s["evidence_index"] = s.get("evidence_index") if isinstance(s.get("evidence_index"), list) else []
    s["metadata"] = s.get("metadata") if isinstance(s.get("metadata"), dict) else {}
    return s


def validate_summary(obj):
    raw_mode = None
    if isinstance(obj, dict) and "mode" in obj:
        raw_mode = obj.get("mode")
    s = normalize_summary(obj)
    errors = []
    if raw_mode is not None and str(raw_mode) != "facts_only":
        errors.append("mode must be facts_only")
    elif s.get("mode") != "facts_only":
        errors.append("mode must be facts_only")
    for k in [
        "project_overview",
        "stack_summary",
        "surface_summary",
        "flow_summary",
        "risk_summary",
        "metadata",
    ]:
        if not isinstance(s.get(k), dict):
            errors.append(f"{k} must be object")
    if not isinstance(s.get("priority_actions"), list):
        errors.append("priority_actions must be array")
    if not isinstance(s.get("evidence_index"), list):
        errors.append("evidence_index must be array")
    return errors


def stable_summary_dumps(obj):
    return json.dumps(normalize_summary(obj), ensure_ascii=False, sort_keys=True)
