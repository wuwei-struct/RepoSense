import json
import os
from collections import defaultdict

from .pattern_rules import run_all_rules
from .pattern_schema import stable_sort_patterns


def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _dedupe_patterns(patterns):
    seen = set()
    out = []
    for p in stable_sort_patterns(patterns):
        key = (str(p.get("pattern_type") or ""), str(p.get("pattern_id") or ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def summarize_patterns(patterns):
    counts_by_type = defaultdict(int)
    counts_by_severity = defaultdict(int)
    counts_by_status = defaultdict(int)
    top_files = defaultdict(int)
    top_languages = defaultdict(int)
    top_frameworks = defaultdict(int)
    for p in patterns:
        counts_by_type[p.get("pattern_type") or "unknown"] += 1
        counts_by_severity[p.get("severity") or "medium"] += 1
        counts_by_status[p.get("status") or "suspected"] += 1
        for f in (p.get("files") or []):
            top_files[f] += 1
        for x in (p.get("languages") or []):
            top_languages[x] += 1
        for x in (p.get("frameworks") or []):
            top_frameworks[x] += 1
    return {
        "total_patterns": len(patterns),
        "counts_by_type": dict(sorted(counts_by_type.items(), key=lambda x: x[0])),
        "counts_by_severity": dict(sorted(counts_by_severity.items(), key=lambda x: x[0])),
        "counts_by_status": dict(sorted(counts_by_status.items(), key=lambda x: x[0])),
        "top_files": [{"file": k, "count": v} for k, v in sorted(top_files.items(), key=lambda x: (-x[1], x[0]))[:10]],
        "top_languages": [{"language": k, "count": v} for k, v in sorted(top_languages.items(), key=lambda x: (-x[1], x[0]))[:10]],
        "top_frameworks": [{"framework": k, "count": v} for k, v in sorted(top_frameworks.items(), key=lambda x: (-x[1], x[0]))[:10]],
    }


def _load_ctx(run_dir):
    report = _read_json(os.path.join(run_dir, "report.json"), {})
    graph = _read_json(os.path.join(run_dir, "event_graph.json"), {"nodes": [], "edges": []})
    return {
        "run_dir": run_dir,
        "findings": report.get("findings") or [],
        "events": graph.get("nodes") or [],
        "event_edges": graph.get("edges") or [],
        "cross_language_summary": _read_json(os.path.join(run_dir, "cross_language_summary.json"), {}),
        "cross_language_links": _read_json(os.path.join(run_dir, "cross_language_links.json"), {}),
    }


def generate_patterns(run_dir):
    ctx = _load_ctx(run_dir)
    pats = run_all_rules(ctx)
    pats = _dedupe_patterns(pats)
    pats = stable_sort_patterns(pats)
    summary = summarize_patterns(pats)
    return pats, summary

