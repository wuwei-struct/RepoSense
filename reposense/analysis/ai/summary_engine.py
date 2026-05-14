import json
import os
from collections import defaultdict

from ...events.taxonomy import normalize_event_kind
from .summary_schema import normalize_summary


def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _safe_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default


def _event_kind_counts(nodes):
    out = defaultdict(int)
    by_path = defaultdict(set)
    for n in nodes or []:
        meta = n.get("meta") or {}
        ek = normalize_event_kind(n.get("type"), meta=meta)
        if not ek:
            continue
        out[ek] += 1
        p = str(meta.get("path") or "")
        if p:
            by_path[p].add(ek)
    return dict(out), by_path


def _top_patterns(patterns, status=None, limit=5):
    sev_rank = {"high": 0, "medium": 1, "low": 2}
    rows = list(patterns or [])
    if status:
        rows = [x for x in rows if str(x.get("status") or "") == status]
    rows.sort(
        key=lambda x: (
            sev_rank.get(str(x.get("severity") or "medium"), 1),
            -float(x.get("confidence") or 0.0),
            str(x.get("pattern_type") or ""),
            str(x.get("pattern_id") or ""),
        )
    )
    return rows[:limit]


def _mk_action(action_id, title, reason, patterns):
    refs = []
    for p in patterns:
        refs.extend(p.get("evidence_refs") or [])
    refs = sorted(
        refs,
        key=lambda x: (
            str((x or {}).get("file") or ""),
            str((x or {}).get("source_type") or ""),
            str((x or {}).get("finding_id") or ""),
            str((x or {}).get("event_id") or ""),
        ),
    )[:8]
    return {
        "action_id": action_id,
        "title": title,
        "reason": reason,
        "related_patterns": sorted(list(set([str(p.get("pattern_id") or "") for p in patterns]))),
        "evidence_refs": refs,
    }


def _priority_actions(patterns, gate):
    acts = []
    confirmed = [p for p in (patterns or []) if p.get("status") == "confirmed"]
    suspected = [p for p in (patterns or []) if p.get("status") == "suspected"]
    by_type = defaultdict(list)
    for p in patterns or []:
        by_type[str(p.get("pattern_type") or "")].append(p)
    if by_type.get("transaction_missing") or by_type.get("db_write_outside_tx"):
        rows = (by_type.get("transaction_missing") or []) + (by_type.get("db_write_outside_tx") or [])
        acts.append(
            _mk_action(
                "action.tx_boundary",
                "先核查写路径事务边界",
                "存在 transaction 缺失或 DB 写入脱离事务的 confirmed/suspected 模式。",
                rows[:3],
            )
        )
    if by_type.get("queue_without_consumer"):
        acts.append(
            _mk_action(
                "action.queue_closure",
                "核查消息消费闭环",
                "存在 queue dispatch 无对应 consume 信号。",
                (by_type.get("queue_without_consumer") or [])[:3],
            )
        )
    if by_type.get("cross_language_api_unmatched"):
        acts.append(
            _mk_action(
                "action.cross_language_match",
                "核查前后端 API 面匹配",
                "cross-language summary 显示 caller/endpoint 未完全匹配。",
                (by_type.get("cross_language_api_unmatched") or [])[:3],
            )
        )
    if len(suspected) >= max(2, len(confirmed)):
        acts.append(
            _mk_action(
                "action.drilldown",
                "对 suspected 模式做二次核查",
                "suspected 模式占比偏高，建议后续 source drill-down 或补规则。",
                suspected[:3],
            )
        )
    gate_status = str((gate or {}).get("status") or "").lower()
    if gate_status in ("warn", "fail"):
        acts.append(
            {
                "action_id": "action.gate_first",
                "title": "优先处理质量门禁告警",
                "reason": f"quality_gate 状态为 {gate_status}，应先处理 violations。",
                "related_patterns": [],
                "evidence_refs": [],
            }
        )
    # stable order + limit
    acts.sort(key=lambda x: str(x.get("action_id") or ""))
    return acts[:5]


def _evidence_index(patterns, actions):
    refs = []
    for p in _top_patterns(patterns, limit=8):
        refs.extend(p.get("evidence_refs") or [])
    for a in actions:
        refs.extend(a.get("evidence_refs") or [])
    seen = set()
    out = []
    for r in refs:
        key = (
            str(r.get("source_type") or ""),
            str(r.get("finding_id") or ""),
            str(r.get("event_id") or ""),
            str(r.get("file") or ""),
            str(r.get("start_line") or 0),
            str(r.get("end_line") or 0),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "source_type": str(r.get("source_type") or ""),
                "finding_id": str(r.get("finding_id") or ""),
                "event_id": str(r.get("event_id") or ""),
                "file": str(r.get("file") or ""),
                "start_line": _safe_int(r.get("start_line") or 0),
                "end_line": _safe_int(r.get("end_line") or 0),
                "rule_id": str(r.get("rule_id") or ""),
            }
        )
        if len(out) >= 20:
            break
    return out


def generate_facts_only_summary(run_dir):
    report = _read_json(os.path.join(run_dir, "report.json"), {})
    graph = _read_json(os.path.join(run_dir, "event_graph.json"), {"nodes": [], "edges": []})
    api_surface = _read_json(os.path.join(run_dir, "api_surface.json"), {})
    coverage = _read_json(os.path.join(run_dir, "coverage.json"), {})
    gate = _read_json(os.path.join(run_dir, "quality_gate.json"), {})
    patterns_obj = _read_json(os.path.join(run_dir, "patterns.json"), {"patterns": []})
    pattern_summary = _read_json(os.path.join(run_dir, "pattern_summary.json"), {})
    run_manifest = _read_json(os.path.join(run_dir, "run_manifest.json"), {})
    entrypoints = _read_json(os.path.join(run_dir, "entrypoints.json"), {})
    cross_summary = _read_json(os.path.join(run_dir, "cross_language_summary.json"), {})
    run_meta = _read_json(os.path.join(run_dir, "manifest.json"), {})

    run_summary = report.get("run_summary") if isinstance(report.get("run_summary"), dict) else {}
    findings = report.get("findings") or []
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    patterns = patterns_obj.get("patterns") if isinstance(patterns_obj, dict) else []

    event_counts, by_path = _event_kind_counts(nodes)
    top_paths = [{"path": p, "event_kinds": sorted(list(ks)), "kind_count": len(ks)} for p, ks in sorted(by_path.items(), key=lambda x: (-len(x[1]), x[0]))[:5]]
    top_families = []
    fam = defaultdict(int)
    for k, v in event_counts.items():
        fam[str(k).split(".")[0]] += int(v)
    for k, v in sorted(fam.items(), key=lambda x: (-x[1], x[0])):
        top_families.append({"family": k, "count": v})

    project_overview = {
        "languages": run_summary.get("detected_languages") or [],
        "frameworks": run_summary.get("detected_frameworks") or [],
        "scanned_files": _safe_int(run_summary.get("scanned_files") or (coverage.get("walk") or {}).get("included_files") or 0),
        "findings": _safe_int(run_summary.get("findings_count") or len(findings)),
        "events": _safe_int(run_summary.get("events_count") or len(nodes)),
        "graph_edges": _safe_int(run_summary.get("graph_edges") or len(edges)),
        "gate_status": str(gate.get("status") or "n/a"),
        "artifact_completeness": {
            "report_json": bool(report),
            "event_graph_json": bool(graph),
            "api_surface_json": bool(api_surface),
            "coverage_json": bool(coverage),
            "quality_gate_json": bool(gate),
            "patterns_json": bool(patterns_obj),
            "pattern_summary_json": bool(pattern_summary),
        },
    }

    stack_summary = {
        "languages": run_summary.get("detected_languages") or [],
        "frameworks": run_summary.get("detected_frameworks") or [],
        "queue_hints": [k for k in event_counts.keys() if str(k).startswith("queue.")],
        "cache_hints": [k for k in event_counts.keys() if str(k).startswith("cache.")],
        "db_hints": [k for k in event_counts.keys() if str(k).startswith("db.")],
        "openapi_present": bool(_safe_int((api_surface.get("stats") or {}).get("by_source_kind", {}).get("openapi", 0)) > 0),
        "cross_language_present": bool(cross_summary),
    }

    surface_summary = {
        "api_count": _safe_int((api_surface.get("stats") or {}).get("unique_endpoints") or len(api_surface.get("endpoints") or [])),
        "write_like_api_count": _safe_int(event_counts.get("db.write", 0) + event_counts.get("queue.dispatch", 0)),
        "queue_dispatch_count": _safe_int(event_counts.get("queue.dispatch", 0)),
        "queue_consume_count": _safe_int(event_counts.get("queue.consume", 0)),
        "cache_read_count": _safe_int(event_counts.get("cache.read", 0)),
        "cache_write_count": _safe_int(event_counts.get("cache.write", 0)),
        "cache_invalidate_count": _safe_int(event_counts.get("cache.invalidate", 0)),
        "db_read_count": _safe_int(event_counts.get("db.read", 0)),
        "db_write_count": _safe_int(event_counts.get("db.write", 0)),
        "db_tx_count": _safe_int(event_counts.get("db.transaction", 0)),
    }

    flow_summary = {
        "top_event_families": top_families,
        "representative_paths": top_paths,
        "cross_language": {
            "matched_links": _safe_int(cross_summary.get("matched_links") or cross_summary.get("exact_match_count") or 0),
            "unmatched_callers": _safe_int(cross_summary.get("unmatched_callers") or 0),
            "unmatched_endpoints": _safe_int(cross_summary.get("endpoints_without_callers") or cross_summary.get("unmatched_endpoints") or 0),
        },
    }

    risk_summary = {
        "total_patterns": _safe_int(pattern_summary.get("total_patterns") or len(patterns)),
        "counts_by_severity": pattern_summary.get("counts_by_severity") or {},
        "counts_by_type": pattern_summary.get("counts_by_type") or {},
        "confirmed_top": [
            {
                "pattern_id": str(p.get("pattern_id") or ""),
                "pattern_type": str(p.get("pattern_type") or ""),
                "severity": str(p.get("severity") or ""),
                "summary": str(p.get("summary") or ""),
            }
            for p in _top_patterns(patterns, status="confirmed", limit=5)
        ],
        "suspected_top": [
            {
                "pattern_id": str(p.get("pattern_id") or ""),
                "pattern_type": str(p.get("pattern_type") or ""),
                "severity": str(p.get("severity") or ""),
                "summary": str(p.get("summary") or ""),
            }
            for p in _top_patterns(patterns, status="suspected", limit=5)
        ],
    }

    actions = _priority_actions(patterns, gate)
    evidence_index = _evidence_index(patterns, actions)
    summary = normalize_summary(
        {
            "version": "ai-summary-v1",
            "run_dir": run_dir,
            "generated_at": str(run_meta.get("timestamp") or ""),
            "mode": "facts_only",
            "project_overview": project_overview,
            "stack_summary": stack_summary,
            "surface_summary": surface_summary,
            "flow_summary": flow_summary,
            "risk_summary": risk_summary,
            "priority_actions": actions,
            "evidence_index": evidence_index,
            "metadata": {
                "gate_status": str(gate.get("status") or ""),
                "warnings_count": _safe_int((coverage.get("warnings") or []) and len(coverage.get("warnings") or [])),
                "entrypoints_count": len(entrypoints.get("entrypoints") or []),
                "manifest_artifacts_count": len(run_manifest.get("artifacts") or []),
            },
        }
    )
    return summary

