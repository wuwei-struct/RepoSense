import os
class RepoSenseConfigError(Exception):
    pass
PROFILES = {
    "demo": {
        "id": "demo",
        "label": "Demo",
        "description": "Open-source demo profile",
        "edition": "oss",
        "ruleset_dir": os.path.join(os.path.dirname(os.path.dirname(__file__)), "rulesets", "demo_v1"),
        "budget_path": os.path.join(os.path.dirname(os.path.dirname(__file__)), "presets", "demo.json"),
        "gate_path": os.path.join(os.path.dirname(os.path.dirname(__file__)), "presets", "gates", "demo.json"),
    },
    "prod_lite": {
        "id": "prod_lite",
        "label": "Prod Lite",
        "description": "Open-source lite profile mapped to demo ruleset",
        "edition": "oss",
        "ruleset_dir": os.path.join(os.path.dirname(os.path.dirname(__file__)), "rulesets", "demo_v1"),
        "budget_path": os.path.join(os.path.dirname(os.path.dirname(__file__)), "presets", "prod_lite.json"),
        "gate_path": os.path.join(os.path.dirname(os.path.dirname(__file__)), "presets", "gates", "prod_lite.json"),
    },
    "prod_deep": {
        "id": "prod_deep",
        "label": "Prod Deep",
        "description": "Enterprise profile (requires enterprise ruleset)",
        "edition": "enterprise",
        "ruleset_dir": os.path.join(os.path.dirname(os.path.dirname(__file__)), "rulesets", "specs_v2"),
        "budget_path": os.path.join(os.path.dirname(os.path.dirname(__file__)), "presets", "prod_deep.json"),
        "gate_path": os.path.join(os.path.dirname(os.path.dirname(__file__)), "presets", "gates", "prod_deep.json"),
    },
}
def resolve_profile(name, edition="oss"):
    name = (name or "demo").lower()
    p = PROFILES.get(name)
    if not p:
        raise RepoSenseConfigError("profile_not_found")
    if p["edition"] == "enterprise" and (edition or "oss") == "oss":
        raise RepoSenseConfigError("enterprise_profile_unavailable")
    return dict(p)
def list_profiles(edition="oss"):
    out = []
    for k in ("demo","prod_lite","prod_deep"):
        p = PROFILES.get(k)
        if not p:
            continue
        if p["edition"] == "enterprise" and (edition or "oss") == "oss":
            continue
        out.append({
            "id": p["id"],
            "label": p["label"],
            "description": p["description"],
            "edition": p["edition"],
            "defaults": {
                "ruleset_dir": p["ruleset_dir"],
                "budget_path": p["budget_path"],
                "gate_path": p["gate_path"],
            }
        })
    return out
def ensure_paths_exist(profile_obj):
    for k in ("ruleset_dir","budget_path","gate_path"):
        p = profile_obj.get(k)
        if not p or not os.path.exists(p):
            raise RepoSenseConfigError(f"path_missing:{k}")
