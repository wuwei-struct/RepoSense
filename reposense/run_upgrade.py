import os
import json
import shutil
from .versioning import generated_by, ruleset_fingerprint
from .run_manifest import build_run_manifest
from .patch_exports import run_patch_exports
def _load(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
def _save(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
def _derive_generated_by(run_dir):
    gb = None
    rm = _load(os.path.join(run_dir, "run_manifest.json")) or {}
    gb = rm.get("generated_by")
    if not gb:
        gb = (_load(os.path.join(run_dir, "quality_gate.json")) or {}).get("generated_by")
    if not gb:
        gb = (_load(os.path.join(run_dir, "report.json")) or {}).get("generated_by")
    if not gb:
        try:
            cfg = _load(os.path.join(run_dir, "meta", "config.json")) or {}
            rsdir = cfg.get("ruleset_dir") or ""
            rid = os.path.basename(rsdir) if rsdir else ""
            rfp = ruleset_fingerprint(rsdir) if rsdir and os.path.isdir(rsdir) else ""
            gb = generated_by("0.1.0", rid, rfp, 1)
            gb["note"] = "legacy_upgrade"
        except Exception:
            gb = generated_by("0.1.0", "", "", 1)
            gb["note"] = "legacy_upgrade"
    return gb
def _stamp_file(path, gb):
    obj = _load(path)
    if obj is None:
        return False
    changed = False
    if obj.get("schema_version") is None:
        obj["schema_version"] = 1
        changed = True
    if obj.get("generated_by") is None:
        obj["generated_by"] = gb
        changed = True
    if changed:
        _save(path, obj)
    return True
def upgrade_run(run_dir, out_dir=None, inplace=True, strict=False, patch_exports=True):
    target = run_dir if inplace or not out_dir else out_dir
    if target != run_dir and out_dir:
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.copytree(run_dir, target)
    run_dir = target
    gb = _derive_generated_by(run_dir)
    changed_any = False
    core = ["report.json","event_graph.json","api_surface.json","entrypoints.json","coverage.json","ci_summary.json","quality_gate.json"]
    for rel in core:
        p = os.path.join(run_dir, rel)
        if os.path.isfile(p):
            _stamp_file(p, gb)
            changed_any = True
    # ensure manifest
    build_run_manifest(run_dir, write=True)
    # patch exports if needed
    if patch_exports:
        try:
            run_patch_exports(run_dir)
        except Exception:
            pass
    if strict and not changed_any:
        return 2
    return 0
