from collections import Counter

from .health_rules import language_for_path
from .health_schema import normalize_maintainability_risk


LIMITATIONS = [
    "Code Health Radar MVP uses deterministic, conservative heuristics.",
    "Function-level size detection is limited in this release.",
    "Test gap detection is inferred from file naming only.",
    "The health score is experimental and is not a correctness or safety proof.",
]


def summarize_code_health(findings):
    by_rule = Counter(f.get("rule_id") for f in findings)
    by_sev = Counter(f.get("severity") for f in findings)
    by_status = Counter(f.get("status") for f in findings)
    by_file = Counter(f.get("file") for f in findings)
    by_lang = Counter(language_for_path(f.get("file") or "") for f in findings)
    penalty = int(by_sev.get("high", 0)) * 12 + int(by_sev.get("medium", 0)) * 6 + int(by_sev.get("low", 0)) * 2
    score = max(0, min(100, 100 - penalty))
    return {
        "total_findings": len(findings),
        "counts_by_rule": dict(sorted((k, int(v)) for k, v in by_rule.items() if k)),
        "counts_by_severity": dict(sorted((k, int(v)) for k, v in by_sev.items() if k)),
        "counts_by_status": dict(sorted((k, int(v)) for k, v in by_status.items() if k)),
        "top_files": [{"file": k, "count": int(v)} for k, v in by_file.most_common(10) if k],
        "top_languages": [{"language": k, "count": int(v)} for k, v in by_lang.most_common(10) if k],
        "health_score": {
            "enabled": True,
            "score": score,
            "note": "experimental heuristic score; not a correctness proof",
        },
        "limitations": LIMITATIONS[:],
    }


def maintainability_risks_from_findings(findings):
    risks = []
    for f in findings:
        if f.get("severity") not in ("high", "medium"):
            continue
        risks.append(
            normalize_maintainability_risk(
                {
                    "risk_id": "mr-" + str(f.get("health_id") or ""),
                    "rule_id": f.get("rule_id"),
                    "title": f.get("title"),
                    "severity": f.get("severity"),
                    "status": f.get("status"),
                    "file": f.get("file"),
                    "reason": f.get("reason"),
                    "evidence_refs": f.get("evidence_refs") or [],
                    "suggested_human_review": True,
                }
            )
        )
    risks.sort(key=lambda r: ({"high": 0, "medium": 1, "low": 2}.get(r.get("severity"), 9), r.get("file"), r.get("rule_id")))
    return {"risks": risks, "limitations": LIMITATIONS[:]}

