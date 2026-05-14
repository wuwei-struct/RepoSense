import json
import os
import time
from collections import Counter, defaultdict


SECTIONS = [
    "API Surface Summary",
    "Backend Events Summary",
    "Transaction Signals",
    "Queue Dispatch Signals",
    "Cache Operation Signals",
    "Side-effect Map",
    "High-risk Findings",
    "Evidence Index",
    "Limitations",
]


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _event_kind(node):
    t = str(node.get("type") or "").lower()
    meta = node.get("meta") or {}
    dbk = str(meta.get("db.kind") or "").lower()
    qk = str(meta.get("queue.kind") or "").lower()
    ck = str(meta.get("cache.kind") or "").lower()
    if "transaction" in t or "tx" in t:
        return "transaction"
    if "queue" in t:
        if "consume" in t:
            return "queue.consume"
        return "queue.dispatch"
    if "cache" in t:
        if "invalidate" in ck or "evict" in ck:
            return "cache.invalidate"
        if "write" in ck or "set" in ck:
            return "cache.write"
        return "cache.read"
    if "db" in t:
        if "write" in dbk or "insert" in dbk or "update" in dbk or "delete" in dbk:
            return "db.write"
        return "db.read"
    if "api" in t or "route" in t:
        return "api"
    return "other"


def _extract_findings(report):
    items = report.get("findings")
    return items if isinstance(items, list) else []


def _extract_events(report, graph):
    nodes = graph.get("nodes")
    if isinstance(nodes, list) and nodes:
        return nodes
    evs = report.get("events")
    return evs if isinstance(evs, list) else []


def _evidence_from_finding(f):
    refs = f.get("evidence_refs")
    if isinstance(refs, list) and refs:
        return refs
    return [{
        "file": f.get("path") or "",
        "start_line": int(f.get("start_line") or 0),
        "end_line": int(f.get("end_line") or 0),
        "rule_id": f.get("rule_id") or "",
        "snippet": f.get("snippet") or "",
        "finding_id": f.get("fid"),
    }]


def _build_side_effect_map(events):
    by_file = defaultdict(lambda: {"api": 0, "db.write": 0, "queue.dispatch": 0, "cache.write": 0})
    for ev in events:
        meta = ev.get("meta") or {}
        f = str(meta.get("path") or ev.get("path") or "")
        if not f:
            continue
        k = _event_kind(ev)
        if k in by_file[f]:
            by_file[f][k] += 1
    rows = []
    for f, c in by_file.items():
        complexity = int(c["db.write"] > 0) + int(c["queue.dispatch"] > 0) + int(c["cache.write"] > 0)
        rows.append({
            "path": f,
            "api_signals": c["api"],
            "db_write_signals": c["db.write"],
            "queue_dispatch_signals": c["queue.dispatch"],
            "cache_write_signals": c["cache.write"],
            "write_path_complexity": complexity,
        })
    rows.sort(key=lambda x: (-x["write_path_complexity"], -x["api_signals"], x["path"]))
    return rows[:20]


def _high_risk_from_patterns(patterns):
    rows = []
    for p in patterns:
        sev = str(p.get("severity") or "low").lower()
        if sev not in ("high", "medium"):
            continue
        ev = p.get("evidence_refs") or []
        rows.append({
            "title": p.get("title") or p.get("pattern_type") or "pattern",
            "risk_level": sev,
            "source": "pattern",
            "why_it_matters": p.get("summary") or "Related backend transaction/side-effect risk signal.",
            "evidence_refs": ev[:5],
            "pattern_id": p.get("pattern_id"),
        })
    return rows


def _high_risk_from_findings(findings):
    rows = []
    for f in findings:
        sev = str(f.get("severity") or "").lower()
        if sev not in ("high", "medium"):
            continue
        refs = _evidence_from_finding(f)
        rows.append({
            "title": f.get("title") or f.get("rule_id") or f"F{f.get('fid')}",
            "risk_level": sev,
            "source": "finding",
            "why_it_matters": "Conservative finding linked to backend transaction or side-effect concerns.",
            "evidence_refs": refs[:5],
            "finding_id": f.get("fid"),
        })
    return rows


def generate_backend_verifier_report(run_dir):
    report = _read_json(os.path.join(run_dir, "report.json"), {})
    graph = _read_json(os.path.join(run_dir, "event_graph.json"), {})
    api_surface = _read_json(os.path.join(run_dir, "api_surface.json"), {})
    coverage = _read_json(os.path.join(run_dir, "coverage.json"), {})
    gate = _read_json(os.path.join(run_dir, "quality_gate.json"), {})
    patterns_obj = _read_json(os.path.join(run_dir, "patterns.json"), {})
    patterns = patterns_obj.get("patterns") if isinstance(patterns_obj.get("patterns"), list) else []

    run_summary = report.get("run_summary") if isinstance(report.get("run_summary"), dict) else {}
    findings = _extract_findings(report)
    events = _extract_events(report, graph)

    kind_counts = Counter()
    lang_counts = Counter()
    fw_counts = Counter()
    for ev in events:
        kind_counts[_event_kind(ev)] += 1
        meta = ev.get("meta") or {}
        if meta.get("language"):
            lang_counts[str(meta.get("language")).lower()] += 1
        if meta.get("framework"):
            fw_counts[str(meta.get("framework")).lower()] += 1

    api_total = int((api_surface.get("stats") or {}).get("unique_endpoints") or len(api_surface.get("endpoints") or []))
    write_like = kind_counts.get("db.write", 0) + kind_counts.get("queue.dispatch", 0) + kind_counts.get("cache.write", 0)
    tx_patterns = [p for p in patterns if str(p.get("pattern_type") or "") in ("transaction_missing", "db_write_outside_tx")]
    queue_unmatched = [p for p in patterns if str(p.get("pattern_type") or "") == "queue_without_consumer"]
    side_effect_map = _build_side_effect_map(events)

    high_risk = _high_risk_from_patterns(patterns)
    if not high_risk:
        high_risk = _high_risk_from_findings(findings)
    high_risk.sort(key=lambda x: (0 if x["risk_level"] == "high" else 1, x["title"]))
    high_risk = high_risk[:20]

    evidence_index = []
    for item in high_risk:
        for ref in (item.get("evidence_refs") or []):
            evidence_index.append({
                "file": ref.get("file") or ref.get("path") or "",
                "start_line": int(ref.get("start_line") or 0),
                "end_line": int(ref.get("end_line") or 0),
                "rule_id": ref.get("rule_id") or "",
                "pattern_id": item.get("pattern_id"),
                "finding_id": item.get("finding_id"),
                "event_id": ref.get("event_id"),
            })
    evidence_index.sort(key=lambda x: (x["file"], x["start_line"], x["end_line"], x["rule_id"]))

    out = {
        "version": 1,
        "report_type": "backend_verifier_report",
        "generated_at": int(time.time()),
        "run_dir": run_dir,
        "sections": SECTIONS[:],
        "api_surface_summary": {
            "api_total": api_total,
            "write_like_api_signals": int(write_like),
            "languages": dict(sorted((run_summary.get("detected_languages") and Counter(run_summary.get("detected_languages")) or lang_counts).items())),
            "frameworks": dict(sorted((run_summary.get("detected_frameworks") and Counter(run_summary.get("detected_frameworks")) or fw_counts).items())),
            "openapi_present": bool(((api_surface.get("stats") or {}).get("by_source_kind") or {}).get("openapi", 0) > 0),
        },
        "backend_events_summary": {
            "counts": {
                "api": int(kind_counts.get("api", 0)),
                "db.read": int(kind_counts.get("db.read", 0)),
                "db.write": int(kind_counts.get("db.write", 0)),
                "transaction": int(kind_counts.get("transaction", 0)),
                "queue.dispatch": int(kind_counts.get("queue.dispatch", 0)),
                "queue.consume": int(kind_counts.get("queue.consume", 0)),
                "cache.read": int(kind_counts.get("cache.read", 0)),
                "cache.write": int(kind_counts.get("cache.write", 0)),
                "cache.invalidate": int(kind_counts.get("cache.invalidate", 0)),
            },
            "top_event_families": [{"family": k, "count": v} for k, v in kind_counts.most_common(8)],
            "languages": dict(sorted(lang_counts.items())),
            "frameworks": dict(sorted(fw_counts.items())),
        },
        "transaction_signals": {
            "transaction_signal_count": int(kind_counts.get("transaction", 0)),
            "transaction_related_patterns": [{
                "pattern_id": p.get("pattern_id"),
                "pattern_type": p.get("pattern_type"),
                "severity": p.get("severity"),
                "status": p.get("status"),
            } for p in tx_patterns],
            "note": "If transaction signal count is 0, it means no transaction signal was observed in current artifacts.",
        },
        "queue_dispatch_signals": {
            "queue_dispatch_count": int(kind_counts.get("queue.dispatch", 0)),
            "queue_consume_count": int(kind_counts.get("queue.consume", 0)),
            "queue_without_consumer_patterns": [{
                "pattern_id": p.get("pattern_id"),
                "severity": p.get("severity"),
                "status": p.get("status"),
            } for p in queue_unmatched],
            "note": "Dispatch without observed consume is a conservative signal, not a proof of missing consumer.",
        },
        "cache_operation_signals": {
            "cache_read_count": int(kind_counts.get("cache.read", 0)),
            "cache_write_count": int(kind_counts.get("cache.write", 0)),
            "cache_invalidate_count": int(kind_counts.get("cache.invalidate", 0)),
            "languages": dict(sorted(lang_counts.items())),
            "frameworks": dict(sorted(fw_counts.items())),
        },
        "side_effect_map": {
            "mode": "conservative_side_effect_map",
            "paths": side_effect_map,
        },
        "high_risk_findings": {
            "gate_status": str(gate.get("status") or ""),
            "items": high_risk,
        },
        "evidence_index": evidence_index,
        "limitations": [
            "Conservative detection based on existing run artifacts.",
            "This report does not guarantee full backend correctness.",
            "Default flow does not perform unrestricted whole-repository source reading.",
            "Side-effect map is a conservative aggregation, not a full call-chain proof.",
            "Some correlations are approximated by file/path-nearby signals.",
        ],
        "metadata": {
            "findings_count": len(findings),
            "events_count": len(events),
            "graph_edges": len(graph.get("edges") or []),
            "included_files": int(((coverage.get("walk") or {}).get("included_files") or 0)),
        },
    }
    return out


def render_backend_verifier_markdown(report):
    ap = report.get("api_surface_summary") or {}
    ev = report.get("backend_events_summary") or {}
    tx = report.get("transaction_signals") or {}
    qq = report.get("queue_dispatch_signals") or {}
    cc = report.get("cache_operation_signals") or {}
    sm = report.get("side_effect_map") or {}
    hr = (report.get("high_risk_findings") or {}).get("items") or []
    ei = report.get("evidence_index") or []
    lim = report.get("limitations") or []

    lines = [
        "# RepoSense Backend Verifier Report",
        "",
        "## 1. API Surface Summary",
        f"- API total: {int(ap.get('api_total') or 0)}",
        f"- Write-like API signals: {int(ap.get('write_like_api_signals') or 0)}",
        f"- OpenAPI present: {bool(ap.get('openapi_present'))}",
        "",
        "## 2. Backend Events Summary",
    ]
    for k, v in (ev.get("counts") or {}).items():
        lines.append(f"- {k}: {int(v or 0)}")
    lines += [
        "",
        "## 3. Transaction Signals",
        f"- Transaction signal count: {int(tx.get('transaction_signal_count') or 0)}",
        f"- Transaction-related patterns: {len(tx.get('transaction_related_patterns') or [])}",
        f"- Note: {tx.get('note') or ''}",
        "",
        "## 4. Queue Dispatch Signals",
        f"- queue.dispatch: {int(qq.get('queue_dispatch_count') or 0)}",
        f"- queue.consume: {int(qq.get('queue_consume_count') or 0)}",
        f"- queue_without_consumer patterns: {len(qq.get('queue_without_consumer_patterns') or [])}",
        "",
        "## 5. Cache Operation Signals",
        f"- cache.read: {int(cc.get('cache_read_count') or 0)}",
        f"- cache.write: {int(cc.get('cache_write_count') or 0)}",
        f"- cache.invalidate: {int(cc.get('cache_invalidate_count') or 0)}",
        "",
        "## 6. Side-effect Map",
        f"- mode: {sm.get('mode') or 'conservative_side_effect_map'}",
    ]
    for row in (sm.get("paths") or [])[:10]:
        lines.append(
            f"- {row.get('path')}: db.write={int(row.get('db_write_signals') or 0)}, "
            f"queue.dispatch={int(row.get('queue_dispatch_signals') or 0)}, "
            f"cache.write={int(row.get('cache_write_signals') or 0)}, "
            f"complexity={int(row.get('write_path_complexity') or 0)}"
        )
    lines += ["", "## 7. High-risk Findings"]
    for item in hr[:10]:
        lines.append(
            f"- [{item.get('risk_level')}] {item.get('title')}: {item.get('why_it_matters')}"
        )
    lines += ["", "## 8. Evidence Index"]
    for ref in ei[:20]:
        lines.append(
            f"- {ref.get('file')}:{int(ref.get('start_line') or 0)}-{int(ref.get('end_line') or 0)} "
            f"rule={ref.get('rule_id') or ''} pattern={ref.get('pattern_id') or ''}"
        )
    lines += ["", "## 9. Limitations"]
    for item in lim:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def export_backend_verifier_report(run_dir, write_json=True, write_markdown=True):
    report = generate_backend_verifier_report(run_dir)
    md = render_backend_verifier_markdown(report)
    json_path = os.path.join(run_dir, "backend_verifier_report.json")
    md_path = os.path.join(run_dir, "backend_verifier_report.md")
    if write_json:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False)
    if write_markdown:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
    try:
        from ...run_manifest import build_run_manifest
        build_run_manifest(run_dir, write=True)
    except Exception:
        pass
    return {
        "report": report,
        "markdown": md,
        "json_path": json_path,
        "markdown_path": md_path,
    }

