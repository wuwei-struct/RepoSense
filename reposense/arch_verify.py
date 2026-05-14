import os
import json
import sqlite3
from pathlib import Path
def verify_arch_views(run_dir, as_json=False):
    out = {"ok": True, "errors": [], "warnings": []}
    av_dir = Path(run_dir) / "arch_views"
    if not av_dir.exists():
        if as_json:
            print(json.dumps({"ok": True, "errors": [], "warnings": ["arch_views_missing"]}))
        else:
            print("ok=true warnings=arch_views_missing")
        return True
    conn = sqlite3.connect(str(Path(run_dir) / "detections.sqlite"))
    eids = set([r[0] for r in conn.cursor().execute("select eid from evidence").fetchall()])
    def check_file(p):
        try:
            data = json.load(open(p, "r", encoding="utf-8"))
        except:
            out["errors"].append(f"parse_failed:{p.name}")
            return
        def visit(obj):
            if isinstance(obj, dict):
                if "evidence" in obj and isinstance(obj["evidence"], list):
                    for ev in obj["evidence"]:
                        try:
                            eid = int(str(ev)[1:]) if str(ev).startswith("E") else int(ev)
                        except:
                            eid = None
                        if not eid or eid not in eids or not (Path(run_dir)/"evidence"/f"E{eid}.json").exists():
                            out["errors"].append(f"missing_evidence:{p.name}:{ev}")
                for v in obj.values():
                    visit(v)
            elif isinstance(obj, list):
                for it in obj:
                    visit(it)
        visit(data)
    for nm in ["api_surface.json","service_map.json","data_surface.json","async_surface.json","deps_surface.json"]:
        fp = av_dir / nm
        if fp.exists():
            check_file(fp)
        else:
            out["warnings"].append(f"missing_view:{nm}")
    try:
        conn.close()
    except:
        pass
    out["ok"] = len(out["errors"]) == 0
    if as_json:
        print(json.dumps(out))
    else:
        print(f"ok={out['ok']} errors={len(out['errors'])} warnings={len(out['warnings'])}")
    return out["ok"]
