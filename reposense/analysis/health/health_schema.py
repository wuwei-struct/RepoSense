import hashlib


VALID_SEVERITIES = {"low", "medium", "high"}
VALID_STATUSES = {"confirmed", "suspected"}


def _clean_text(value, limit=240):
    text = " ".join(str(value or "").split())
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def make_health_id(rule_id, file, line_start, snippet="", signals=None):
    parts = [
        str(rule_id or ""),
        str(file or "").replace("\\", "/"),
        str(int(line_start or 0)),
        _clean_text(snippet, limit=120),
        ",".join(sorted(str(x) for x in (signals or []))),
    ]
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:12]
    return "ch-" + digest


def normalize_health_finding(item):
    x = item if isinstance(item, dict) else {}
    severity = str(x.get("severity") or "low").lower()
    if severity not in VALID_SEVERITIES:
        severity = "low"
    status = str(x.get("status") or "suspected").lower()
    if status not in VALID_STATUSES:
        status = "suspected"
    signals = x.get("signals") if isinstance(x.get("signals"), list) else []
    file_path = str(x.get("file") or "").replace("\\", "/")
    line_start = int(x.get("line_start") or 1)
    snippet = _clean_text(x.get("snippet"), limit=300)
    rule_id = str(x.get("rule_id") or "")
    return {
        "health_id": str(x.get("health_id") or make_health_id(rule_id, file_path, line_start, snippet, signals)),
        "rule_id": rule_id,
        "category": str(x.get("category") or "code_health"),
        "title": _clean_text(x.get("title"), limit=160),
        "severity": severity,
        "status": status,
        "confidence": float(x.get("confidence") or 0.0),
        "file": file_path,
        "line_start": line_start,
        "line_end": int(x.get("line_end") or line_start),
        "snippet": snippet,
        "signals": [str(v) for v in signals if str(v or "").strip()],
        "reason": _clean_text(x.get("reason"), limit=320),
        "evidence_refs": x.get("evidence_refs") if isinstance(x.get("evidence_refs"), list) else [],
        "metadata": x.get("metadata") if isinstance(x.get("metadata"), dict) else {},
    }


def normalize_maintainability_risk(item):
    x = item if isinstance(item, dict) else {}
    return {
        "risk_id": str(x.get("risk_id") or ""),
        "source": "code_health",
        "rule_id": str(x.get("rule_id") or ""),
        "title": _clean_text(x.get("title"), limit=160),
        "severity": str(x.get("severity") or "low").lower(),
        "status": str(x.get("status") or "suspected").lower(),
        "file": str(x.get("file") or "").replace("\\", "/"),
        "reason": _clean_text(x.get("reason"), limit=320),
        "evidence_refs": x.get("evidence_refs") if isinstance(x.get("evidence_refs"), list) else [],
        "suggested_human_review": bool(x.get("suggested_human_review", True)),
    }

