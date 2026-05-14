import os
import json
import zipfile
def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}
def patch_sarif_with_gate(run_dir, sarif_path, gate_path):
    if not os.path.isfile(gate_path):
        return {"ok": False, "error": "quality_gate.json missing"}
    if not os.path.isfile(sarif_path):
        return {"ok": False, "error": "sarif missing"}
    gate = _read_json(gate_path, {"status": "N/A"})
    sarif = _read_json(sarif_path, {})
    try:
        runs = sarif.get("runs") or []
        if runs:
            props = runs[0].get("properties") or {}
            props["reposense.gate_status"] = gate.get("status", "N/A")
            runs[0]["properties"] = props
            with open(sarif_path, "w", encoding="utf-8") as f:
                json.dump(sarif, f, ensure_ascii=False)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
def patch_context_pack_with_gate(run_dir, context_pack_dir, zip_path, gate_path):
    if not os.path.isfile(gate_path):
        return {"ok": False, "error": "quality_gate.json missing"}
    if not os.path.isdir(context_pack_dir):
        return {"ok": False, "error": "context_pack dir missing"}
    try:
        art_dir = os.path.join(context_pack_dir, "ARTIFACTS")
        os.makedirs(art_dir, exist_ok=True)
        data = _read_json(gate_path, {})
        with open(os.path.join(art_dir, "quality_gate.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        if zip_path:
            os.makedirs(os.path.dirname(zip_path), exist_ok=True)
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for base, _, files in os.walk(context_pack_dir):
                    for fn in files:
                        p = os.path.join(base, fn)
                        rel = os.path.relpath(p, context_pack_dir).replace("\\", "/")
                        zf.write(p, arcname=rel)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
def run_patch_exports(run_dir):
    sarif = os.path.join(run_dir, "exports", "report.sarif.json")
    gate = os.path.join(run_dir, "quality_gate.json")
    ctx_dir = os.path.join(run_dir, "context_pack")
    ctx_zip = os.path.join(run_dir, "exports", "context_pack.zip")
    r1 = patch_sarif_with_gate(run_dir, sarif, gate)
    if not r1.get("ok"):
        print(json.dumps(r1))
        return 2
    r2 = patch_context_pack_with_gate(run_dir, ctx_dir, ctx_zip, gate)
    if not r2.get("ok"):
        print(json.dumps(r2))
        return 2
    print(json.dumps({"ok": True}))
    return 0
