import hashlib


def normalize_risk_item(item):
    x = item if isinstance(item, dict) else {}
    return {
        "risk_id": str(x.get("risk_id") or ""),
        "title": str(x.get("title") or ""),
        "severity": str(x.get("severity") or "medium"),
        "status": str(x.get("status") or "suspected"),
        "priority_score": float(x.get("priority_score") or 0.0),
        "pattern_type": str(x.get("pattern_type") or ""),
        "description": str(x.get("description") or ""),
        "why_it_matters": str(x.get("why_it_matters") or ""),
        "evidence_refs": x.get("evidence_refs") if isinstance(x.get("evidence_refs"), list) else [],
        "snippet_refs": x.get("snippet_refs") if isinstance(x.get("snippet_refs"), list) else [],
        "related_patterns": x.get("related_patterns") if isinstance(x.get("related_patterns"), list) else [],
        "related_findings": x.get("related_findings") if isinstance(x.get("related_findings"), list) else [],
        "related_events": x.get("related_events") if isinstance(x.get("related_events"), list) else [],
        "recommended_action": str(x.get("recommended_action") or ""),
        "next_check": str(x.get("next_check") or ""),
        "confirmed": x.get("confirmed") if isinstance(x.get("confirmed"), list) else [],
        "suspected": x.get("suspected") if isinstance(x.get("suspected"), list) else [],
        "unknown": x.get("unknown") if isinstance(x.get("unknown"), list) else [],
    }


def normalize_risks_report(report):
    r = report if isinstance(report, dict) else {}
    items = [normalize_risk_item(x) for x in (r.get("risk_items") or [])]
    return {
        "report_id": str(r.get("report_id") or ""),
        "run_dir": str(r.get("run_dir") or ""),
        "mode": str(r.get("mode") or "facts_only"),
        "summary": r.get("summary") if isinstance(r.get("summary"), dict) else {},
        "risk_items": items,
        "priority_actions": r.get("priority_actions") if isinstance(r.get("priority_actions"), list) else [],
        "evidence_index": r.get("evidence_index") if isinstance(r.get("evidence_index"), list) else [],
        "limitations": r.get("limitations") if isinstance(r.get("limitations"), list) else [],
        "metadata": r.get("metadata") if isinstance(r.get("metadata"), dict) else {},
    }


def make_report_id(run_dir, with_drilldown=False):
    key = f"{str(run_dir or '')}|{bool(with_drilldown)}"
    return "rk-" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
