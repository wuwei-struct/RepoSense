import os
import re
import hashlib
from .path_normalize import normalize_path, template_match

_HTTP_VERBS = {"GET", "POST", "PUT", "DELETE", "PATCH"}


def _infer_lang_fw(source_kind):
    sk = str(source_kind or "")
    if sk == "openapi":
        return "openapi", "openapi"
    if sk.startswith("python"):
        return "python", "fastapi"
    if sk.startswith("typescript"):
        return "typescript", "express"
    if sk.startswith("java"):
        return "java", "spring"
    return "unknown", "unknown"


def _resolve_import_target(base_dir, imp):
    p = str(imp or "").strip().strip('"').strip("'")
    if not p.startswith("."):
        return ""
    cand = []
    rp = os.path.normpath(os.path.join(base_dir, p))
    cand.append(rp)
    cand.extend([rp + ".ts", rp + ".tsx", rp + ".mts", rp + ".cts", os.path.join(rp, "index.ts"), os.path.join(rp, "index.tsx")])
    for c in cand:
        if os.path.isfile(c):
            return c
    return ""


def _collect_ts_router_prefix_map(repo_root):
    pref = {}
    if not repo_root or not os.path.isdir(repo_root):
        return pref
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "dist", "build"}]
        for nm in files:
            if not nm.lower().endswith((".ts", ".tsx", ".mts", ".cts")):
                continue
            fp = os.path.join(root, nm)
            try:
                lines = open(fp, "r", encoding="utf-8", errors="ignore").read().splitlines()
            except Exception:
                continue
            alias_to_target = {}
            for ln in lines:
                mi = re.search(r"import\s+([A-Za-z_][A-Za-z0-9_]*)\s+from\s+(['\"][^'\"]+['\"])", ln)
                if mi:
                    target = _resolve_import_target(root, mi.group(2))
                    if target:
                        alias_to_target[mi.group(1)] = target
            for ln in lines:
                mu = re.search(r"app\.use\s*\(\s*(['\"])([^'\"]+)\1\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)", ln)
                if not mu:
                    continue
                pfx = normalize_path(mu.group(2))
                alias = mu.group(3)
                tgt = alias_to_target.get(alias)
                if not tgt:
                    continue
                rel = os.path.relpath(tgt, repo_root).replace("\\", "/")
                pref.setdefault(rel, [])
                if pfx not in pref[rel]:
                    pref[rel].append(pfx)
    return pref


def build_endpoint_index(api_surface, graph=None, repo_root=None):
    out = []
    prefix_map = _collect_ts_router_prefix_map(repo_root)
    gmap = {}
    for n in (graph or {}).get("nodes", []):
        if str(n.get("type") or "") != "api":
            continue
        meta = n.get("meta") or {}
        k = (
            str(meta.get("http.method") or "").upper(),
            normalize_path(meta.get("http.path") or ""),
            str(meta.get("path") or "").replace("\\", "/"),
            int(meta.get("start_line") or 0),
        )
        gmap[k] = meta
    for ep in (api_surface.get("endpoints") or []):
        src = ep.get("source") or {}
        method = str(ep.get("method") or "").upper()
        if method not in _HTTP_VERBS:
            continue
        path = normalize_path(ep.get("path") or "")
        sk = ep.get("source_kind")
        lang, fw = _infer_lang_fw(sk)
        k = (method, path, str(src.get("path") or "").replace("\\", "/"), int(src.get("start_line") or 0))
        meta = gmap.get(k) or {}
        if meta.get("language"):
            lang = meta.get("language")
        if meta.get("framework"):
            fw = meta.get("framework")
        fpath = str(src.get("path") or "")
        rel_fpath = fpath.replace("\\", "/")
        if repo_root:
            try:
                ab = os.path.abspath(fpath)
                rr = os.path.abspath(repo_root)
                if ab.startswith(rr):
                    rel_fpath = os.path.relpath(ab, rr).replace("\\", "/")
            except Exception:
                rel_fpath = fpath.replace("\\", "/")
        if lang == "unknown":
            lp = fpath.lower()
            if lp.endswith(".py"):
                lang = "python"
            elif lp.endswith((".ts", ".tsx", ".mts", ".cts")):
                lang = "typescript"
            elif lp.endswith((".yaml", ".yml", ".json")):
                lang = "openapi"
            elif lp.endswith(".java"):
                lang = "java"
        if fw == "unknown" and lang == "java":
            fw = "spring"
        npath_out = path
        if lang == "typescript" and rel_fpath in prefix_map:
            best = []
            for pfx in prefix_map.get(rel_fpath) or []:
                best.append(normalize_path(pfx.rstrip("/") + "/" + path.lstrip("/")))
            if best:
                npath_out = sorted(best)[0]
        out.append({
            "endpoint_id": ep.get("id"),
            "method": method,
            "path": npath_out,
            "path_normalized": npath_out,
            "language": lang,
            "framework": fw,
            "source_kind": sk,
            "file": fpath,
            "line_start": int(src.get("start_line") or 0),
            "line_end": int(src.get("end_line") or 0),
            "evidence_ref": src.get("evidence_ref"),
        })
    out.sort(key=lambda x: (x["method"], x["path_normalized"], x["language"], x["framework"], x["file"] or "", x["line_start"]))
    return out


def match_callers_to_endpoints(callers, endpoints):
    links = []
    caller_matched = set()
    endpoint_matched = set()
    by_method = {}
    for ep in endpoints:
        by_method.setdefault(ep.get("method"), []).append(ep)
    for m in by_method:
        by_method[m] = sorted(by_method[m], key=lambda x: (x["path_normalized"], x["endpoint_id"] or ""))
    for c in callers:
        method = c.get("http_method")
        cpath = c.get("path_normalized")
        eps = by_method.get(method) or []
        best = None
        mtype = ""
        for ep in eps:
            if cpath == ep.get("path_normalized"):
                best = ep
                mtype = "exact_match"
                break
        if not best:
            for ep in eps:
                if template_match(ep.get("path_normalized"), cpath):
                    best = ep
                    mtype = "template_match"
                    break
        if not best:
            continue
        conf = 0.95 if mtype == "exact_match" else 0.8
        conf = min(conf, float(c.get("confidence") or conf))
        caller_id = c.get("caller_id")
        endpoint_id = best.get("endpoint_id")
        link_id = hashlib.sha1(f"{caller_id}|{endpoint_id}|{mtype}".encode("utf-8")).hexdigest()
        links.append({
            "link_id": link_id,
            "caller_id": caller_id,
            "endpoint_id": endpoint_id,
            "match_type": mtype,
            "confidence": conf,
            "language_pair": f'{c.get("language","unknown")}->{best.get("language","unknown")}',
            "method": method,
            "caller_path": cpath,
            "endpoint_path": best.get("path_normalized"),
            "evidence_refs": [caller_id, best.get("evidence_ref")],
            "caller": {"file": c.get("file"), "line_start": c.get("line_start"), "line_end": c.get("line_end")},
            "endpoint": {"file": best.get("file"), "line_start": best.get("line_start"), "line_end": best.get("line_end")},
        })
        caller_matched.add(caller_id)
        endpoint_matched.add(endpoint_id)
    links.sort(key=lambda x: (x["match_type"], -float(x["confidence"]), x["method"], x["caller_path"], x["endpoint_path"], x["link_id"]))
    unmatched_callers = [c for c in callers if c.get("caller_id") not in caller_matched]
    unmatched_endpoints = [e for e in endpoints if e.get("endpoint_id") not in endpoint_matched]
    unmatched_callers.sort(key=lambda x: (x.get("file") or "", int(x.get("line_start") or 0), x.get("http_method") or "", x.get("path_normalized") or ""))
    unmatched_endpoints.sort(key=lambda x: (x.get("method") or "", x.get("path_normalized") or "", x.get("file") or "", int(x.get("line_start") or 0)))
    return {"links": links, "unmatched_callers": unmatched_callers, "unmatched_endpoints": unmatched_endpoints}
