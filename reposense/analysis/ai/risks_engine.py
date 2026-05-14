import json
import os
from collections import defaultdict

from .explain_export import export_ai_explain
from .explain_engine import generate_explain_result
from .risks_ranker import rank_risk_items
from .risks_schema import make_report_id, normalize_risks_report


def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _severity_ok(sev, threshold):
    rank = {"high": 3, "medium": 2, "low": 1}
    return rank.get(str(sev or "low"), 1) >= rank.get(str(threshold or "medium"), 2)


def _mk_risk_from_pattern(p, explain=None, snippet_pack_ref=None):
    ex = explain if isinstance(explain, dict) else {}
    confirmed = ex.get("confirmed") if isinstance(ex.get("confirmed"), list) else []
    inferred = ex.get("inferred") if isinstance(ex.get("inferred"), list) else []
    unknown = ex.get("unknown") if isinstance(ex.get("unknown"), list) else []
    snippets = []
    if isinstance(snippet_pack_ref, dict):
        jp = str(snippet_pack_ref.get("json_path") or "")
        if jp and os.path.isfile(jp):
            try:
                obj = _read_json(jp, {})
                for s in obj.get("selected_snippets") or []:
                    snippets.append(
                        {
                            "snippet_id": str(s.get("snippet_id") or ""),
                            "file": str(s.get("file") or ""),
                            "line_start": int(s.get("line_start") or 0),
                            "line_end": int(s.get("line_end") or 0),
                        }
                    )
            except Exception:
                pass
    return {
        "risk_id": "risk-" + str(p.get("pattern_id") or ""),
        "title": str(p.get("title") or p.get("pattern_type") or "risk"),
        "severity": str(p.get("severity") or "medium"),
        "status": str(p.get("status") or "suspected"),
        "pattern_type": str(p.get("pattern_type") or ""),
        "description": str(p.get("summary") or ""),
        "why_it_matters": "This pattern may impact correctness, consistency, or service reliability.",
        "evidence_refs": p.get("evidence_refs") if isinstance(p.get("evidence_refs"), list) else [],
        "snippet_refs": snippets,
        "related_patterns": [str(p.get("pattern_id") or "")],
        "related_findings": [str(x) for x in (p.get("supporting_findings") or [])],
        "related_events": [str(x) for x in (p.get("supporting_events") or [])],
        "recommended_action": str(p.get("explain_stub") or "Review pattern evidence and confirm implementation boundary."),
        "next_check": "Validate against latest run and confirm if risk is mitigated.",
        "confirmed": confirmed,
        "suspected": inferred,
        "unknown": unknown,
        "confidence": float(p.get("confidence") or 0.0),
    }


def generate_risks_report(
    run_dir,
    with_drilldown=False,
    no_drilldown=False,
    max_auto_drilldowns=5,
    severity_threshold="medium",
):
    patterns_obj = _read_json(os.path.join(run_dir, "patterns.json"), {"patterns": []})
    psummary = _read_json(os.path.join(run_dir, "pattern_summary.json"), {})
    ai_summary = _read_json(os.path.join(run_dir, "ai_summary.json"), {})
    gate = _read_json(os.path.join(run_dir, "quality_gate.json"), {})
    patterns = patterns_obj.get("patterns") if isinstance(patterns_obj, dict) else []
    auto_dd_used = 0
    risk_items = []
    for p in patterns:
        pid = str(p.get("pattern_id") or "")
        st = str(p.get("status") or "suspected")
        sev = str(p.get("severity") or "medium")
        facts_explain = generate_explain_result(run_dir, "pattern", pid, with_drilldown=False, no_drilldown=True)
        need_auto_dd = (
            (not no_drilldown)
            and _severity_ok(sev, severity_threshold)
            and st == "suspected"
            and (
                with_drilldown
                or len(p.get("evidence_refs") or []) < 2
                or len(facts_explain.get("unknown") or []) > 0
            )
            and auto_dd_used < int(max_auto_drilldowns or 5)
        )
        explain = facts_explain
        snippet_ref = {}
        if need_auto_dd:
            ex = export_ai_explain(
                run_dir,
                target_type="pattern",
                target_id=pid,
                with_drilldown=True,
                no_drilldown=False,
            )
            explain = ex.get("result") or facts_explain
            snippet_ref = explain.get("snippet_pack_ref") if isinstance(explain.get("snippet_pack_ref"), dict) else {}
            auto_dd_used += 1
        risk_items.append(_mk_risk_from_pattern(p, explain=explain, snippet_pack_ref=snippet_ref))

    ranked = rank_risk_items(risk_items, gate_obj=gate)
    counts_by_status = defaultdict(int)
    counts_by_sev = defaultdict(int)
    for x in ranked:
        counts_by_status[str(x.get("status") or "suspected")] += 1
        counts_by_sev[str(x.get("severity") or "medium")] += 1
    evidence_index = []
    seen = set()
    for item in ranked:
        for r in item.get("evidence_refs") or []:
            key = (
                str(r.get("source_type") or ""),
                str(r.get("finding_id") or ""),
                str(r.get("event_id") or ""),
                str(r.get("file") or ""),
                str(r.get("start_line") or ""),
                str(r.get("end_line") or ""),
            )
            if key in seen:
                continue
            seen.add(key)
            evidence_index.append(r)
            if len(evidence_index) >= 30:
                break
        if len(evidence_index) >= 30:
            break

    top = ranked[:5]
    priority_actions = []
    for x in top:
        priority_actions.append(
            {
                "title": f"Address {str(x.get('pattern_type') or 'risk')}",
                "risk_id": str(x.get("risk_id") or ""),
                "reason": str(x.get("description") or ""),
                "recommended_action": str(x.get("recommended_action") or ""),
            }
        )

    mode = "facts_plus_targeted_drilldown" if auto_dd_used > 0 else "facts_only"
    report = normalize_risks_report(
        {
            "report_id": make_report_id(run_dir, with_drilldown=(auto_dd_used > 0)),
            "run_dir": run_dir,
            "mode": mode,
            "summary": {
                "total_risks": len(ranked),
                "counts_by_status": dict(sorted(counts_by_status.items(), key=lambda x: x[0])),
                "counts_by_severity": dict(sorted(counts_by_sev.items(), key=lambda x: x[0])),
                "gate_status": str(gate.get("status") or "n/a"),
                "top_pattern_types": psummary.get("counts_by_type") if isinstance(psummary.get("counts_by_type"), dict) else {},
                "summary_context": {
                    "project_overview": ai_summary.get("project_overview") if isinstance(ai_summary.get("project_overview"), dict) else {},
                },
            },
            "risk_items": ranked,
            "priority_actions": priority_actions,
            "evidence_index": evidence_index,
            "limitations": [
                "Risk report is facts-first and deterministic.",
                "Targeted drilldown is limited to suspected medium/high risks under budget.",
                "No unrestricted full-repository source reading is performed.",
            ],
            "metadata": {
                "auto_drilldowns_used": auto_dd_used,
                "max_auto_drilldowns": int(max_auto_drilldowns or 5),
                "severity_threshold": str(severity_threshold or "medium"),
            },
        }
    )
    return report
