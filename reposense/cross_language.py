import os
import json
from .parsers.ts_http_callers import collect_ts_http_callers
from .linking.cross_language_matcher import build_endpoint_index, match_callers_to_endpoints


def build_cross_language_exports(run_dir):
    cfg = {}
    try:
        with open(os.path.join(run_dir, "meta", "config.json"), "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    repo_root = cfg.get("repo_root") or ""
    if not repo_root:
        try:
            with open(os.path.join(run_dir, "manifest.json"), "r", encoding="utf-8") as f:
                man = json.load(f)
            repo_root = man.get("repo_root") or ""
        except Exception:
            repo_root = ""
    repo_root = repo_root or run_dir
    api = {}
    try:
        with open(os.path.join(run_dir, "api_surface.json"), "r", encoding="utf-8") as f:
            api = json.load(f)
    except Exception:
        api = {"endpoints": []}
    graph = {}
    try:
        with open(os.path.join(run_dir, "event_graph.json"), "r", encoding="utf-8") as f:
            graph = json.load(f)
    except Exception:
        graph = {"nodes": []}
    gb = {}
    try:
        with open(os.path.join(run_dir, "report.json"), "r", encoding="utf-8") as f:
            gb = json.load(f).get("generated_by") or {}
    except Exception:
        gb = {"tool": "reposense", "reposense_version": "0.1.0", "schema_version": 1}
    callers_obj = collect_ts_http_callers(repo_root)
    callers = callers_obj.get("callers") or []
    unsupported = callers_obj.get("unsupported") or []
    endpoints = build_endpoint_index(api, graph, repo_root=repo_root)
    matched = match_callers_to_endpoints(callers, endpoints)
    links = matched.get("links") or []
    unmatched_callers = matched.get("unmatched_callers") or []
    unmatched_endpoints = matched.get("unmatched_endpoints") or []
    pairs = {}
    exact_count = 0
    template_count = 0
    for l in links:
        p = l.get("language_pair") or "unknown->unknown"
        pairs[p] = pairs.get(p, 0) + 1
        if l.get("match_type") == "exact_match":
            exact_count += 1
        elif l.get("match_type") == "template_match":
            template_count += 1
    for u in unmatched_endpoints[:100]:
        unsupported.append({
            "type": "unsupported_detected",
            "language": u.get("language"),
            "framework": u.get("framework"),
            "path": u.get("file"),
            "line_start": u.get("line_start"),
            "reason": "saw_endpoint_but_no_caller_matched",
        })
    for u in unmatched_callers[:100]:
        unsupported.append({
            "type": "unsupported_detected",
            "language": "typescript",
            "framework": u.get("client_kind"),
            "path": u.get("file"),
            "line_start": u.get("line_start"),
            "reason": "saw_caller_but_no_endpoint_matched",
        })
    unsupported.sort(key=lambda x: (str(x.get("path") or ""), int(x.get("line_start") or 0), str(x.get("reason") or "")))
    api_callers = {
        "schema_version": 1,
        "callers": callers,
        "unsupported_detected": unsupported,
        "generated_by": gb,
    }
    links_obj = {
        "schema_version": 1,
        "links": links,
        "unmatched_callers": unmatched_callers,
        "unmatched_endpoints": unmatched_endpoints,
        "generated_by": gb,
    }
    summary = {
        "schema_version": 1,
        "total_callers": len(callers),
        "matched_callers": len(callers) - len(unmatched_callers),
        "unmatched_callers": len(unmatched_callers),
        "total_endpoints": len(endpoints),
        "endpoints_with_callers": len(endpoints) - len(unmatched_endpoints),
        "endpoints_without_callers": len(unmatched_endpoints),
        "exact_match_count": exact_count,
        "template_match_count": template_count,
        "links_by_language_pair": {k: pairs[k] for k in sorted(pairs.keys())},
        "generated_by": gb,
    }
    topology = {
        "schema_version": 1,
        "endpoints": endpoints,
        "callers": callers,
        "links": links,
        "generated_by": gb,
    }
    with open(os.path.join(run_dir, "api_callers.json"), "w", encoding="utf-8") as f:
        json.dump(api_callers, f, ensure_ascii=False)
    with open(os.path.join(run_dir, "cross_language_links.json"), "w", encoding="utf-8") as f:
        json.dump(links_obj, f, ensure_ascii=False)
    with open(os.path.join(run_dir, "cross_language_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False)
    with open(os.path.join(run_dir, "api_topology.json"), "w", encoding="utf-8") as f:
        json.dump(topology, f, ensure_ascii=False)
    return {
        "api_callers": api_callers,
        "cross_language_links": links_obj,
        "cross_language_summary": summary,
        "api_topology": topology,
    }
