import os
import re
import json
import hashlib
import sqlite3
from .utils import write_json

_VERBS = {"get", "post", "put", "delete", "patch"}


def _normalize_path(p):
    if not p:
        return ""
    s = p.strip()
    s = s.replace("\\", "/")
    s = re.sub(r"[/]+", "/", s)
    s = re.sub(r"<([a-zA-Z_][a-zA-Z0-9_]*)>", r"{\1}", s)
    s = re.sub(r":([a-zA-Z_][a-zA-Z0-9_]*)", r"{\1}", s)
    s = re.sub(r"\{([^\}]+)\}", lambda m: "{" + m.group(1).strip() + "}", s)
    if s != "/" and s.endswith("/"):
        s = s[:-1]
    if not s.startswith("/"):
        s = "/" + s
    return s


def _source_kind(meta, parse_level):
    k = (meta or {}).get("evidence_strength")
    if k:
        return k
    if parse_level == "L2":
        return "openapi"
    if parse_level == "L3":
        return "python_ast"
    return "text"


def _confidence_for_source(src):
    if src == "openapi":
        return 1.0
    if src == "python_ast":
        return 0.9
    if src in ("typescript_l2", "java_l2"):
        return 0.85
    return 0.6


def _stable_id(method, npath, src, path, s, e):
    h = hashlib.sha1()
    h.update((method or "").upper().encode("utf-8"))
    h.update(b"|")
    h.update((npath or "").encode("utf-8"))
    h.update(b"|")
    h.update((src or "").encode("utf-8"))
    h.update(b"|")
    h.update((path or "").replace("\\","/").encode("utf-8"))
    h.update(b"|")
    h.update(str(int(s or 0)).encode("utf-8"))
    h.update(b"|")
    h.update(str(int(e or 0)).encode("utf-8"))
    return h.hexdigest()


def _extract_method_path_from_meta_or_snippet(meta, snippet):
    m = meta or {}
    method = (m.get("http.method") or "").upper()
    path = m.get("http.path")
    if not (method and path) and snippet:
        fx = re.search(r"@(app|router)\.(get|post|put|delete|patch)\s*\(\s*(['\"])([^'\"]+)\3", snippet)
        if fx:
            method = fx.group(2).upper()
            path = fx.group(4)
            return method, path
        fl = re.search(r"@(app|bp)\.route\s*\(\s*(['\"])([^'\"]+)\2", snippet)
        if fl:
            path = fl.group(3)
            mm = re.search(r"methods\s*=\s*\[([^\]]+)\]", snippet, flags=re.I)
            if mm:
                m1 = re.search(r"['\"](GET|POST|PUT|DELETE|PATCH)['\"]", mm.group(1), flags=re.I)
                if m1:
                    method = m1.group(1).upper()
            if not method:
                method = "GET"
            return method, path
        parts = snippet.strip().split()
        if len(parts) >= 2:
            method = parts[0].upper()
            path = parts[1]
    return method, path


def _openapi_yaml_endpoints(file_path):
    out = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except Exception:
        return out
    in_paths = False
    current_path = ""
    for i, line in enumerate(lines, start=1):
        raw = line.rstrip("\n")
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("paths:"):
            in_paths = True
            continue
        if not in_paths:
            continue
        mpath = re.match(r"^\s{0,6}(/[^:\s]+)\s*:\s*$", raw)
        if mpath:
            current_path = mpath.group(1)
            continue
        mverb = re.match(r"^\s{2,12}([a-zA-Z]+)\s*:\s*$", raw)
        if mverb and current_path:
            vb = mverb.group(1).lower()
            if vb in _VERBS:
                out.append((vb.upper(), current_path, i))
    return out


def _openapi_json_endpoints(file_path):
    out = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except Exception:
        return out
    paths = (obj.get("paths") or {}) if isinstance(obj, dict) else {}
    for pth in sorted(paths.keys()):
        m = paths.get(pth) or {}
        if not isinstance(m, dict):
            continue
        for vb in sorted(m.keys()):
            if str(vb).lower() in _VERBS:
                out.append((str(vb).upper(), pth, 1))
    return out


def build_api_surface(run_dir):
    report = {}
    try:
        with open(os.path.join(run_dir, "report.json"), "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception:
        report = {"findings": []}
    rows = []
    try:
        conn = sqlite3.connect(os.path.join(run_dir, "detections.sqlite"))
        c = conn.cursor()
        rows = c.execute("select f.fid, f.concept, f.rule_id, f.confidence, f.parse_level, f.primary_eid, f.meta_json, e.path, e.start_line, e.end_line, e.snippet from findings f join evidence e on e.eid=f.primary_eid where f.concept='API'").fetchall()
    except Exception:
        rows = []
    endpoints = []
    for fid, concept, rule_id, conf, level, eid, mj, path, s, e, snip in rows:
        meta = {}
        try:
            meta = json.loads(mj or "{}")
        except Exception:
            meta = {}
        method, raw_path = _extract_method_path_from_meta_or_snippet(meta, snip)
        if not (method and raw_path):
            continue
        src = _source_kind(meta, level)
        npath = _normalize_path(raw_path)
        nid = _stable_id(method, npath, src, path, s, e)
        endpoints.append({
            "id": nid,
            "method": method,
            "path": npath,
            "source_kind": src,
            "source": {"path": path, "start_line": int(s or 0), "end_line": int(e or 0), "evidence_ref": f"E{eid}"},
            "tags": meta.get("openapi.tags") or [],
            "summary": meta.get("openapi.summary"),
            "language": meta.get("language"),
            "framework": meta.get("framework"),
            "class_name": meta.get("controller_class") or meta.get("class_name"),
            "method_name": meta.get("handler_method") or meta.get("method_name"),
            "confidence": _confidence_for_source(src),
            "normalized_key": f"{method} {npath}",
        })
    try:
        conn.close()
    except Exception:
        pass
    # fallback using report.json if no rows
    if not endpoints:
        for f in (report.get("findings") or []):
            if (f.get("concept") or "") != "API":
                continue
            meta = {}
            # fetch meta_json from detections.sqlite
            try:
                conn = sqlite3.connect(os.path.join(run_dir, "detections.sqlite"))
                c = conn.cursor()
                row = c.execute("select meta_json from findings where fid=?", (int(f.get("fid") or 0),)).fetchone()
                if row:
                    meta = json.loads(row[0] or "{}")
                conn.close()
            except Exception:
                meta = {}
            method, raw_path = _extract_method_path_from_meta_or_snippet(meta, f.get("snippet"))
            if not (method and raw_path):
                continue
            src = _source_kind(meta, f.get("parse_level"))
            npath = _normalize_path(raw_path)
            nid = _stable_id(method, npath, src, f.get("path"), f.get("start_line"), f.get("end_line"))
            endpoints.append({
                "id": nid,
                "method": method,
                "path": npath,
                "source_kind": src,
                "source": {"path": f.get("path"), "start_line": int(f.get("start_line") or 0), "end_line": int(f.get("end_line") or 0), "evidence_ref": f"E{f.get('primary_eid')}"},
                "tags": meta.get("openapi.tags") or [],
                "summary": meta.get("openapi.summary"),
                "language": meta.get("language"),
                "framework": meta.get("framework"),
                "class_name": meta.get("controller_class") or meta.get("class_name"),
                "method_name": meta.get("handler_method") or meta.get("method_name"),
                "confidence": _confidence_for_source(src),
                "normalized_key": f"{method} {npath}",
            })
    seen_ids = set([x.get("id") for x in endpoints])
    repo_root = ""
    try:
        with open(os.path.join(run_dir, "manifest.json"), "r", encoding="utf-8") as f:
            man = json.load(f)
        repo_root = man.get("repo_root") or ""
    except Exception:
        repo_root = ""
    if repo_root and os.path.isdir(repo_root):
        for root, dirs, files in os.walk(repo_root):
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "dist", "build"}]
            for nm in sorted(files):
                low = nm.lower()
                if not (low.endswith(".yaml") or low.endswith(".yml") or low.endswith(".json")):
                    continue
                if not any(x in low for x in ["openapi", "swagger"]):
                    continue
                fp = os.path.join(root, nm)
                pairs = _openapi_yaml_endpoints(fp) if (low.endswith(".yaml") or low.endswith(".yml")) else _openapi_json_endpoints(fp)
                rel = os.path.relpath(fp, repo_root).replace("\\", "/")
                for method, raw_path, sline in pairs:
                    npath = _normalize_path(raw_path)
                    nid = _stable_id(method, npath, "openapi", rel, sline, sline)
                    if nid in seen_ids:
                        continue
                    seen_ids.add(nid)
                    endpoints.append({
                        "id": nid,
                        "method": method,
                        "path": npath,
                        "source_kind": "openapi",
                        "source": {"path": rel, "start_line": int(sline or 0), "end_line": int(sline or 0), "evidence_ref": ""},
                        "tags": [],
                        "summary": None,
                        "language": "openapi",
                        "framework": "openapi",
                        "class_name": "",
                        "method_name": "",
                        "confidence": 1.0,
                        "normalized_key": f"{method} {npath}",
                    })
    # stats
    by_src = {}
    for ep in endpoints:
        by_src[ep["source_kind"]] = by_src.get(ep["source_kind"], 0) + 1
    dup = {}
    for ep in endpoints:
        dup.setdefault(ep["normalized_key"], []).append(ep["id"])
    duplicate_routes = [{"normalized_key": k, "count": len(v)} for k, v in dup.items() if len(v) > 1]
    # mismatches
    spec_keys = set([ep["normalized_key"] for ep in endpoints if ep["source_kind"] == "openapi"])
    code_keys = set([ep["normalized_key"] for ep in endpoints if ep["source_kind"] != "openapi"])
    missing_in_spec = sorted(list(code_keys - spec_keys))
    missing_in_code = sorted(list(spec_keys - code_keys))
    # method mismatch: same normalized path ignoring method
    def path_only(key): return key.split(" ", 1)[1] if " " in key else key
    spec_paths = {}
    code_paths = {}
    for k in spec_keys:
        spec_paths.setdefault(path_only(k), set()).add(k.split(" ", 1)[0])
    for k in code_keys:
        code_paths.setdefault(path_only(k), set()).add(k.split(" ", 1)[0])
    method_mismatch = []
    for p in sorted(set(spec_paths.keys()) & set(code_paths.keys())):
        if spec_paths[p] != code_paths[p]:
            method_mismatch.append({"path": p, "spec_methods": sorted(list(spec_paths[p])), "code_methods": sorted(list(code_paths[p]))})
    # optional path_suspect: simple prefix-only heuristic
    path_suspect = []
    for ck in sorted(code_keys):
        cm, cp = ck.split(" ", 1)
        for sk in sorted(spec_keys):
            sm, sp = sk.split(" ", 1)
            if cm == sm and (cp.startswith(sp) or sp.startswith(cp)) and cp != sp:
                path_suspect.append({"method": cm, "code_path": cp, "spec_path": sp, "confidence": 0.5})
                break
    try:
        with open(os.path.join(run_dir, "meta", "config.json"), "r", encoding="utf-8") as f:
            cfg = json.load(f)
        rsdir = cfg.get("ruleset_dir") or ""
        from .versioning import ruleset_fingerprint, generated_by
        rid = os.path.basename(rsdir) if rsdir else ""
        rfp = ruleset_fingerprint(rsdir) if rsdir and os.path.isdir(rsdir) else ""
        gb = generated_by("0.1.0", rid, rfp, 1)
    except Exception:
        gb = {"tool":"reposense","reposense_version":"0.1.0","ruleset_id":"","ruleset_fingerprint":"","schema_version":1}
    api_surface = {
        "schema_version": 1,
        "endpoints": sorted(endpoints, key=lambda x: (x["normalized_key"], x["source_kind"], x["source"]["path"], x["source"]["start_line"])),
        "stats": {
            "by_source_kind": by_src,
            "unique_endpoints": len(set([ep["normalized_key"] for ep in endpoints])),
            "duplicate_routes": duplicate_routes
        },
        "mismatches": {
            "missing_in_spec": missing_in_spec,
            "missing_in_code": missing_in_code,
            "method_mismatch": method_mismatch,
            "path_suspect": path_suspect
        },
        "generated_by": gb
    }
    write_json(os.path.join(run_dir, "api_surface.json"), api_surface)
    return api_surface
