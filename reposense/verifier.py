import os
import json
import sqlite3
def run_verify(run_dir, as_json, strict=False):
    res = verify(run_dir, strict=strict)
    out = json.dumps(res) if as_json else format_text(res)
    print(out)
    if strict and not res.get("ok", False):
        raise SystemExit(2)
    # non-strict never fails hard; only exceptions cause exit=1
def format_text(res):
    lines = []
    lines.append(f"ok={res['ok']}")
    if res["errors"]:
        lines.append("errors:")
        lines.extend([f"- {e}" for e in res["errors"]])
    if res["warnings"]:
        lines.append("warnings:")
        lines.extend([f"- {w}" for w in res["warnings"]])
    return "\n".join(lines)
def verify(run_dir, strict=False):
    errors = []
    warnings = []
    required_files = [
        "indices.sqlite",
        "detections.sqlite",
        "report.json",
        "report.html",
        os.path.join("meta", "tool_version.json"),
        os.path.join("meta", "ruleset_version.json"),
        os.path.join("meta", "config.json")
    ]
    for rf in required_files:
        if not os.path.exists(os.path.join(run_dir, rf)):
            (errors if strict else warnings).append(f"missing file: {rf}")
    repo_root = ""
    try:
        with open(os.path.join(run_dir, "manifest.json"), "r", encoding="utf-8") as f:
            manifest = json.load(f)
        rr = manifest.get("repo_root")
        if rr:
            repo_root = rr
    except Exception:
        pass
    with open(os.path.join(run_dir, "meta", "config.json"), "r", encoding="utf-8") as cf:
        cfg = json.load(cf)
    budget = cfg.get("budget", {})
    repo_root = repo_root or (cfg.get("repo_root", "") or run_dir)
    max_snippet_lines = int(budget.get("max_snippet_lines", 400))
    conn = None
    c = None
    if os.path.exists(os.path.join(run_dir, "detections.sqlite")):
        try:
            conn = sqlite3.connect(os.path.join(run_dir, "detections.sqlite"))
            c = conn.cursor()
        except Exception:
            conn = None
            c = None
    if c:
        try:
            ev_rows = c.execute("select eid, path, start_line, end_line, snippet, sha256, parse_level from evidence").fetchall()
        except Exception:
            ev_rows = []
        for eid, path, s, e, snip, sha, level in ev_rows:
            if level not in ("L1", "L2", "L3"):
                errors.append(f"evidence {eid} invalid parse_level {level}")
            try:
                real = os.path.abspath(path)
                base = os.path.abspath(repo_root)
                if os.path.commonpath([real, base]) != base:
                    (errors if strict else warnings).append(f"evidence {eid} path outside repo_root")
            except Exception as ex:
                (errors if strict else warnings).append(f"evidence {eid} path check failed")
            if not isinstance(snip, str):
                errors.append(f"evidence {eid} snippet missing")
            else:
                lines = snip.splitlines()
                if len(lines) > max_snippet_lines:
                    (errors if strict else warnings).append(f"evidence {eid} snippet exceeds budget")
    try:
        fid_rows = c.execute("select fid, primary_eid from findings").fetchall() if c else []
    except Exception:
        fid_rows = []
    try:
        fe_rows = c.execute("select fid, eid from finding_evidence").fetchall() if c else []
    except Exception:
        fe_rows = []
    try:
        ev_ids = set([r[0] for r in c.execute("select eid from evidence").fetchall()]) if c else set()
    except Exception:
        ev_ids = set()
    for fid, pe in fid_rows:
        if pe not in ev_ids:
            errors.append(f"finding {fid} primary_eid missing")
    for fid, eid in fe_rows:
        if eid not in ev_ids:
            errors.append(f"finding_evidence link missing eid {eid}")
    # verify event_graph references
    try:
        with open(os.path.join(run_dir, "event_graph.json"), "r", encoding="utf-8") as gf:
            graph = json.load(gf)
        # edge type enumeration
        allowed_types = {"declares","declares_dependency","observed_in_same_scope","supported_by","encloses_tx","uses_cache","dispatches_job","cache_within_tx","dispatch_within_tx"}
        for e in graph.get("edges", []):
            t = e.get("type")
            if t not in allowed_types:
                (errors if strict else warnings).append(f"unknown edge.type: {t}")
        node_ids = set([n["event_id"] for n in graph.get("nodes", [])])
        # verify nodes exist in events table (by type+key)
        ev_map = set([(r[0], r[1]) for r in c.execute("select type, key from events").fetchall()]) if c else set()
        # check node evidence exists
        ev_ids = set([r[0] for r in c.execute("select eid from evidence").fetchall()]) if c else set()
        for n in graph.get("nodes", []):
            if (n.get("type"), n.get("key")) not in ev_map:
                errors.append(f"graph node missing in events table type={n.get('type')} key={n.get('key')}")
            for ev in n.get("evidence", []):
                try:
                    eid = int(ev[1:])
                except:
                    eid = None
                if eid is None or eid not in ev_ids:
                    errors.append(f"graph node {n['event_id']} references missing evidence {ev}")
                else:
                    # also check file exists
                    pjson = os.path.join(run_dir, "evidence", f"{ev}.json")
                    if not os.path.exists(pjson):
                        errors.append(f"graph node {n['event_id']} evidence file missing {ev}")
        # check edges
        for e in graph.get("edges", []):
            if e["type"] in ["declares","declares_dependency","observed_in_same_scope"]:
                if e.get("from") not in node_ids or e.get("to") not in node_ids:
                    errors.append("graph edge declares references missing node")
            for ev in e.get("evidence", []):
                try:
                    eid = int(ev[1:])
                except:
                    eid = None
                if eid is None or eid not in ev_ids:
                    errors.append("graph edge references missing evidence")
    except Exception:
        pass
    # verify api_surface
    ap = os.path.join(run_dir, "api_surface.json")
    if not os.path.exists(ap):
        errors.append("api_surface.json missing")
    else:
        try:
            with open(ap, "r", encoding="utf-8") as f:
                surf = json.load(f)
            eps = surf.get("endpoints", [])
            st = surf.get("stats", {}) or {}
            if st.get("unique_endpoints", 0) < 0:
                errors.append("api_surface stats invalid")
            ev_ids_set = set([r[0] for r in c.execute("select eid from evidence").fetchall()]) if c else set()
            for ep in eps:
                ref = ((ep.get("source") or {}).get("evidence_ref") or "")
                if ref:
                    try:
                        eid = int(ref[1:])
                    except Exception:
                        eid = None
                    if eid is None or eid not in ev_ids_set:
                        errors.append("api_surface endpoint evidence missing")
        except Exception:
            errors.append("api_surface verify failed")
    epf = os.path.join(run_dir, "entrypoints.json")
    if not os.path.exists(epf):
        errors.append("entrypoints.json missing")
    else:
        try:
            with open(epf, "r", encoding="utf-8") as f:
                ents = json.load(f)
            lst = ents.get("entrypoints", [])
            for e in lst:
                if not e.get("id") or not e.get("kind") or not e.get("title"):
                    errors.append("entrypoint missing required fields")
                cf = e.get("confidence")
                if cf is None or not (0 <= float(cf) <= 1):
                    errors.append("entrypoint confidence out of range")
        except Exception:
            errors.append("entrypoints verify failed")
    # stamps check (non-strict: warn; strict: error)
    def _require_stamp(path, name):
        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            if obj.get("schema_version") is None or obj.get("generated_by") is None:
                (errors if strict else warnings).append(f"{name} missing stamp")
        except Exception:
            (errors if strict else warnings).append(f"{name} read failed")
    for rel, nm in [("report.json","report"),("event_graph.json","event_graph"),("api_surface.json","api_surface"),("entrypoints.json","entrypoints"),("coverage.json","coverage")]:
        p = os.path.join(run_dir, rel)
        if os.path.isfile(p):
            _require_stamp(p, nm)
        else:
            (errors if strict else warnings).append(f"{nm} missing")
    # baseline diff required when baseline_used
    try:
        with open(os.path.join(run_dir, "quality_gate.json"), "r", encoding="utf-8") as f:
            qg = json.load(f)
        if qg.get("baseline_used"):
            bd = os.path.join(run_dir, "baseline_diff.json")
            if not os.path.exists(bd):
                errors.append("baseline_diff.json missing")
            else:
                try:
                    with open(bd, "r", encoding="utf-8") as f:
                        obj = json.load(f)
                    if obj.get("schema_version") != 1:
                        errors.append("baseline_diff schema_version invalid")
                    for k in ("added","removed","severity_changed"):
                        if k not in obj:
                            errors.append("baseline_diff missing arrays")
                    gb = obj.get("generated_by")
                    if not gb or gb.get("schema_version") != 1:
                        errors.append("baseline_diff generated_by missing")
                except Exception:
                    errors.append("baseline_diff verify failed")
            gbq = qg.get("generated_by")
            if not gbq or gbq.get("schema_version") != 1:
                errors.append("quality_gate generated_by missing")
    except Exception:
        pass
    ok = len(errors) == 0
    # strict: run_manifest must exist and hashes match
    if strict:
        rm = os.path.join(run_dir, "run_manifest.json")
        if not os.path.isfile(rm):
            errors.append("run_manifest.json missing")
        else:
            try:
                import hashlib
                with open(rm, "r", encoding="utf-8") as f:
                    obj = json.load(f)
                arts = obj.get("artifacts") or []
                for a in arts:
                    rel = a.get("path")
                    p = os.path.join(run_dir, rel)
                    if os.path.isfile(p):
                        with open(p, "rb") as f:
                            h = hashlib.sha256(f.read()).hexdigest()
                        if h != a.get("sha256"):
                            errors.append(f"run_manifest sha mismatch: {rel}")
            except Exception:
                errors.append("run_manifest verify failed")
    try:
        if conn:
            conn.close()
    except:
        pass
    return {"ok": ok, "errors": errors, "warnings": warnings}
