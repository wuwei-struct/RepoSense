import json
import os

from .drilldown_export import export_drilldown
from .explain_schema import build_explain_request, normalize_explain_result


def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _safe_int(x, d=0):
    try:
        return int(x)
    except Exception:
        return int(d)


def _event_ref(node):
    meta = node.get("meta") or {}
    return {
        "source_type": "event",
        "event_id": str(node.get("event_id") or ""),
        "file": str(meta.get("path") or ""),
        "start_line": _safe_int(meta.get("start_line"), 0),
        "end_line": _safe_int(meta.get("end_line"), 0),
        "rule_id": "",
    }


def _finding_ref(f):
    return {
        "source_type": "finding",
        "finding_id": str(f.get("fid") or ""),
        "file": str(f.get("path") or ""),
        "start_line": _safe_int(f.get("start_line"), 0),
        "end_line": _safe_int(f.get("end_line"), 0),
        "rule_id": str(f.get("rule_id") or ""),
    }


def _needs_drilldown(target_type, target, with_drilldown=False, no_drilldown=False):
    if no_drilldown:
        return False, "disabled_by_flag"
    if with_drilldown:
        return True, "forced_by_flag"
    if target_type == "pattern":
        status = str(target.get("status") or "")
        refs = target.get("evidence_refs") or []
        ptype = str(target.get("pattern_type") or "")
        if status == "suspected":
            return True, "suspected_pattern"
        if len(refs) < 2:
            return True, "insufficient_evidence_refs"
        if ptype in ("transaction_missing", "db_write_outside_tx", "api_write_without_idempotency_guard"):
            return True, "implementation_boundary_pattern"
    if target_type in ("finding", "event"):
        refs = 0
        if target_type == "finding":
            refs = 1 if str(target.get("path") or "") else 0
        else:
            refs = 1 if str((target.get("meta") or {}).get("path") or "") else 0
        if refs < 1:
            return True, "insufficient_location_info"
    return False, "facts_sufficient"


def _collect_snippet_refs(snippet_pack):
    out = []
    if not isinstance(snippet_pack, dict):
        return out
    for s in snippet_pack.get("selected_snippets") or []:
        out.append(
            {
                "snippet_id": str(s.get("snippet_id") or ""),
                "file": str(s.get("file") or ""),
                "line_start": _safe_int(s.get("line_start"), 0),
                "line_end": _safe_int(s.get("line_end"), 0),
            }
        )
    return out


def _explain_pattern(p):
    refs = p.get("evidence_refs") or []
    ptype = str(p.get("pattern_type") or "")
    status = str(p.get("status") or "suspected")
    confirmed = [
        {
            "claim": f"Pattern `{ptype}` is detected for target `{str(p.get('pattern_id') or '')}`.",
            "because": str(p.get("summary") or "Pattern rule matched on facts."),
            "evidence_refs": refs[:6],
            "snippet_refs": [],
            "confidence": float(p.get("confidence") or 0.0),
        }
    ]
    if refs:
        confirmed.append(
            {
                "claim": f"Pattern has {len(refs)} evidence reference(s).",
                "because": "Evidence references were emitted by deterministic pattern rules.",
                "evidence_refs": refs[:6],
                "snippet_refs": [],
                "confidence": 0.8,
            }
        )
    inferred = [
        {
            "claim": "Implementation detail may exist outside current fact coverage.",
            "signals": [ptype, status],
            "why_not_confirmed": "Current explain flow does not perform unrestricted source traversal.",
            "evidence_refs": refs[:4],
            "snippet_refs": [],
        }
    ]
    unknown = [
        {
            "question": "Is this behavior fully guarded across all service boundaries?",
            "missing_evidence": ["cross-file transaction/order boundary", "runtime execution context"],
            "suggested_next_step": "Use drilldown snippets or targeted architecture review for boundary validation.",
        }
    ]
    return confirmed, inferred, unknown


def _explain_finding(f, related_patterns):
    ref = _finding_ref(f)
    confirmed = [
        {
            "claim": f"Finding `{str(f.get('fid') or '')}` is present in report.",
            "because": f"Rule `{str(f.get('rule_id') or '')}` matched at {str(f.get('path') or '')}.",
            "evidence_refs": [ref],
            "snippet_refs": [],
            "confidence": float(f.get("confidence") or 0.0),
        }
    ]
    inferred = [
        {
            "claim": "Finding may indicate risk propagation to surrounding write/read path.",
            "signals": [str(f.get("concept") or ""), str(f.get("rule_id") or "")],
            "why_not_confirmed": "Propagation scope is not directly encoded in finding-only facts.",
            "evidence_refs": [ref],
            "snippet_refs": [],
        }
    ]
    unknown = [
        {
            "question": "What exact implementation branch triggers this finding in production flow?",
            "missing_evidence": ["branch-level runtime path", "cross-function control flow"],
            "suggested_next_step": "Run drilldown on this finding and inspect nearby code branches.",
        }
    ]
    if related_patterns:
        confirmed.append(
            {
                "claim": f"{len(related_patterns)} related pattern(s) include this finding context.",
                "because": "Pattern evidence overlaps file/range or supporting finding linkage.",
                "evidence_refs": [ref],
                "snippet_refs": [],
                "confidence": 0.7,
            }
        )
    return confirmed, inferred, unknown


def _explain_event(e, related_patterns):
    ref = _event_ref(e)
    et = str(e.get("type") or "")
    confirmed = [
        {
            "claim": f"Event `{str(e.get('event_id') or '')}` is recorded in event graph.",
            "because": f"Event type `{et}` appears with source location metadata.",
            "evidence_refs": [ref],
            "snippet_refs": [],
            "confidence": float(e.get("confidence") or 0.0),
        }
    ]
    inferred = [
        {
            "claim": "This event is likely part of a larger structural chain.",
            "signals": [et, str((e.get("meta") or {}).get("path") or "")],
            "why_not_confirmed": "Event graph neighborhood interpretation is shallow in explain v1.",
            "evidence_refs": [ref],
            "snippet_refs": [],
        }
    ]
    unknown = [
        {
            "question": "What upstream/downstream steps are semantically coupled with this event?",
            "missing_evidence": ["deep path semantics", "runtime ordering constraints"],
            "suggested_next_step": "Use drilldown and correlate with neighboring events manually.",
        }
    ]
    if related_patterns:
        inferred.append(
            {
                "claim": f"Event is associated with {len(related_patterns)} pattern(s).",
                "signals": [str(x.get("pattern_type") or "") for x in related_patterns[:3]],
                "why_not_confirmed": "Association is evidence-linked but not full causal proof.",
                "evidence_refs": [ref],
                "snippet_refs": [],
            }
        )
    return confirmed, inferred, unknown


def generate_explain_result(run_dir, target_type, target_id, with_drilldown=False, no_drilldown=False):
    req = build_explain_request(target_type, target_id, with_drilldown=with_drilldown, no_drilldown=no_drilldown)
    report = _read_json(os.path.join(run_dir, "report.json"), {})
    graph = _read_json(os.path.join(run_dir, "event_graph.json"), {"nodes": [], "edges": []})
    patterns_obj = _read_json(os.path.join(run_dir, "patterns.json"), {"patterns": []})
    patterns = patterns_obj.get("patterns") if isinstance(patterns_obj, dict) else []
    findings = report.get("findings") or []
    events = graph.get("nodes") or []
    target = None
    related_patterns = []

    if req["target_type"] == "pattern":
        target = next((x for x in patterns if str(x.get("pattern_id") or "") == req["target_id"]), None)
        if not target:
            raise ValueError("pattern_id not found")
        confirmed, inferred, unknown = _explain_pattern(target)
    elif req["target_type"] == "finding":
        target = next((x for x in findings if str(x.get("fid") or "") == req["target_id"]), None)
        if not target:
            raise ValueError("finding_id not found")
        related_patterns = [p for p in patterns if req["target_id"] in [str(x) for x in (p.get("supporting_findings") or [])]]
        confirmed, inferred, unknown = _explain_finding(target, related_patterns)
    else:
        target = next((x for x in events if str(x.get("event_id") or "") == req["target_id"]), None)
        if not target:
            raise ValueError("event_id not found")
        related_patterns = [p for p in patterns if req["target_id"] in [str(x) for x in (p.get("supporting_events") or [])]]
        confirmed, inferred, unknown = _explain_event(target, related_patterns)

    should_drill, reason = _needs_drilldown(
        req["target_type"], target, with_drilldown=req["with_drilldown"], no_drilldown=req["no_drilldown"]
    )
    mode = "facts_only"
    snippet_pack_ref = {}
    snippet_refs = []
    if should_drill:
        dd = export_drilldown(
            run_dir,
            target_type=req["target_type"],
            target_id=req["target_id"],
            budget={"max_files": 5, "max_snippets": 6, "max_lines_per_snippet": 80, "context_lines": 25, "max_total_chars": 12000},
        )
        mode = "facts_plus_drilldown"
        snippet_pack_ref = {
            "request_id": str(dd.get("request_id") or ""),
            "json_path": str(dd.get("json_path") or ""),
            "markdown_path": str(dd.get("markdown_path") or ""),
        }
        snippet_refs = _collect_snippet_refs(dd.get("pack") or {})
        for c in confirmed:
            c["snippet_refs"] = snippet_refs[:3]
        for i in inferred:
            i["snippet_refs"] = snippet_refs[:2]

    evidence_index = []
    for row in confirmed:
        evidence_index.extend(row.get("evidence_refs") or [])
    for row in inferred:
        evidence_index.extend(row.get("evidence_refs") or [])
    seen = set()
    uniq = []
    for r in evidence_index:
        key = (
            str(r.get("source_type") or ""),
            str(r.get("finding_id") or ""),
            str(r.get("event_id") or ""),
            str(r.get("file") or ""),
            _safe_int(r.get("start_line"), 0),
            _safe_int(r.get("end_line"), 0),
            str(r.get("rule_id") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)

    result = normalize_explain_result(
        {
            "request_id": req["request_id"],
            "run_dir": run_dir,
            "target_type": req["target_type"],
            "target_id": req["target_id"],
            "mode": mode,
            "confirmed": confirmed,
            "inferred": inferred,
            "unknown": unknown,
            "evidence_index": uniq[:20],
            "snippet_pack_ref": snippet_pack_ref,
            "limitations": [
                "Default explanation is facts-first.",
                "If drilldown is used, only evidence-constrained snippets are read.",
                "No unrestricted full-repository source reading is performed.",
            ],
            "metadata": {
                "drilldown_triggered": bool(should_drill),
                "drilldown_reason": reason,
            },
        }
    )
    return result
