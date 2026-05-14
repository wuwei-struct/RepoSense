import os
import json
from .adapters.registry import list_registered_languages, get_adapter, get_capability_matrix
from .events.normalize import collect_detected_languages_frameworks


def build_language_capabilities(run_dir):
    report = {}
    graph = {}
    api_surface = {}
    entrypoints = {}
    try:
        with open(os.path.join(run_dir, "report.json"), "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception:
        report = {}
    try:
        with open(os.path.join(run_dir, "event_graph.json"), "r", encoding="utf-8") as f:
            graph = json.load(f)
    except Exception:
        graph = {"nodes": [], "edges": []}
    try:
        with open(os.path.join(run_dir, "api_surface.json"), "r", encoding="utf-8") as f:
            api_surface = json.load(f)
    except Exception:
        api_surface = {"endpoints": []}
    try:
        with open(os.path.join(run_dir, "entrypoints.json"), "r", encoding="utf-8") as f:
            entrypoints = json.load(f)
    except Exception:
        entrypoints = {"entrypoints": []}
    findings = report.get("findings") or []
    nodes = graph.get("nodes") or []
    detected_languages, detected_frameworks = collect_detected_languages_frameworks(findings, nodes)
    matrix = get_capability_matrix()
    observed = {}
    for lid in list_registered_languages():
        ad = get_adapter(lid)
        if not ad:
            continue
        evs = ad.emit_events(run_dir, graph=graph)
        aps = ad.emit_api_surface(run_dir, api_surface=api_surface)
        eps = ad.emit_entrypoints(run_dir, entrypoints=entrypoints)
        observed[lid] = {
            "framework_hints_detected": sorted(list(ad.detect_framework_hints(run_dir, findings=findings, graph=graph) or [])),
            "events_emitted": len(evs),
            "api_surface_items": len(aps),
            "entrypoints_items": len(eps),
        }
    out = {
        "schema_version": 1,
        "registered_languages": list_registered_languages(),
        "capability_matrix": matrix,
        "detected_languages": detected_languages,
        "detected_frameworks": detected_frameworks,
        "observed_by_language": observed,
    }
    p = os.path.join(run_dir, "language_capabilities.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    return out
