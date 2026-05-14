import hashlib
import json

ALLOWED_SEVERITY = {"low", "medium", "high"}
ALLOWED_STATUS = {"confirmed", "suspected"}


def evidence_token(ref):
    r = ref or {}
    return "|".join(
        [
            str(r.get("source_type") or ""),
            str(r.get("finding_id") or ""),
            str(r.get("event_id") or ""),
            str(r.get("file") or ""),
            str(r.get("start_line") or 0),
            str(r.get("end_line") or 0),
            str(r.get("rule_id") or ""),
        ]
    )


def make_pattern_id(pattern_type, evidence_refs):
    toks = sorted([evidence_token(x) for x in (evidence_refs or [])])
    src = str(pattern_type or "") + "||" + "||".join(toks)
    return hashlib.sha1(src.encode("utf-8")).hexdigest()[:12]


def normalize_pattern(raw):
    p = dict(raw or {})
    p["pattern_type"] = str(p.get("pattern_type") or "")
    p["severity"] = str(p.get("severity") or "medium").lower()
    p["status"] = str(p.get("status") or "suspected").lower()
    p["confidence"] = round(float(p.get("confidence") or 0.0), 3)
    p["supporting_findings"] = sorted(
        [str(x) for x in (p.get("supporting_findings") or []) if str(x).strip() != ""]
    )
    p["supporting_events"] = sorted(
        [str(x) for x in (p.get("supporting_events") or []) if str(x).strip() != ""]
    )
    p["evidence_refs"] = sorted(
        (p.get("evidence_refs") or []),
        key=lambda x: (
            str((x or {}).get("file") or ""),
            int((x or {}).get("start_line") or 0),
            str((x or {}).get("source_type") or ""),
            str((x or {}).get("finding_id") or ""),
            str((x or {}).get("event_id") or ""),
        ),
    )
    p["files"] = sorted(set([str(x) for x in (p.get("files") or [])]))
    p["languages"] = sorted(set([str(x) for x in (p.get("languages") or [])]))
    p["frameworks"] = sorted(set([str(x) for x in (p.get("frameworks") or [])]))
    p["metadata"] = p.get("metadata") if isinstance(p.get("metadata"), dict) else {}
    p["explain_stub"] = str(p.get("explain_stub") or "")
    if not p.get("pattern_id"):
        p["pattern_id"] = make_pattern_id(p["pattern_type"], p["evidence_refs"])
    return p


def validate_pattern(pat):
    p = normalize_pattern(pat)
    errors = []
    if not p.get("pattern_id"):
        errors.append("pattern_id missing")
    if not p.get("pattern_type"):
        errors.append("pattern_type missing")
    if p.get("severity") not in ALLOWED_SEVERITY:
        errors.append("severity invalid")
    if p.get("status") not in ALLOWED_STATUS:
        errors.append("status invalid")
    if float(p.get("confidence") or 0.0) < 0 or float(p.get("confidence") or 0.0) > 1:
        errors.append("confidence out of range")
    if not isinstance(p.get("evidence_refs"), list):
        errors.append("evidence_refs invalid")
    if len(p.get("evidence_refs") or []) == 0:
        errors.append("evidence_refs empty")
    return errors


def stable_sort_patterns(patterns):
    sev_rank = {"high": 0, "medium": 1, "low": 2}
    return sorted(
        [normalize_pattern(p) for p in (patterns or [])],
        key=lambda x: (
            sev_rank.get(x.get("severity") or "medium", 1),
            str(x.get("pattern_type") or ""),
            str(x.get("pattern_id") or ""),
        ),
    )


def stable_dumps(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)
