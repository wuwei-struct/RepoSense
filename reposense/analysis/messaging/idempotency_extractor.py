import re
from pathlib import Path


STRONG_GUARDS = {
    "persistent_guard_observed",
    "redis_atomic_guard_observed",
    "unique_constraint_observed",
    "inbox_or_processed_event_observed",
}
SIDE_EFFECT_KINDS = {
    "db.write",
    "cache.write",
    "cache.invalidate",
    "queue.dispatch",
}


def _brace_end(lines, start):
    depth = 0
    seen = False
    quote = ""
    escaped = False
    for index in range(start, len(lines)):
        for char in lines[index]:
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = ""
                continue
            if char in "\"'`":
                quote = char
            elif char == "{":
                depth += 1
                seen = True
            elif char == "}":
                depth -= 1
        if seen and depth <= 0:
            return index + 1
    return 0


def _java_handler_range(lines, anchor):
    method = re.compile(
        r"\b(?:public|protected|private)?\s*(?:static\s+)?"
        r"(?:<[^>]+>\s*)?[\w$.<>\[\],?]+\s+"
        r"([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^;]*\)"
        r"(?:\s+throws\s+[^{]+)?\s*\{"
    )
    for index in range(max(0, anchor - 1), min(len(lines), anchor + 16)):
        if method.search(lines[index]):
            end = _brace_end(lines, index)
            return (index + 1, end) if end else (0, 0)
    return 0, 0


def _typescript_method_range(lines, anchor, consumer_style):
    if consumer_style == "nest_processor":
        pattern = re.compile(
            r"\b(?:async\s+)?process\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{"
        )
        start_at = anchor
    else:
        pattern = re.compile(r"(?:=>|function\s*\([^)]*\))\s*\{")
        start_at = max(0, anchor - 1)
    for index in range(start_at, min(len(lines), start_at + 80)):
        if pattern.search(lines[index]):
            end = _brace_end(lines, index)
            return (index + 1, end) if end else (0, 0)
    return 0, 0


def _method_definitions(lines):
    definitions = {}
    pattern = re.compile(
        r"^\s*(?:public|protected|private)?\s*(?:async\s+)?"
        r"([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^;]*\)"
        r"(?:\s*:\s*[^{]+)?\s*\{"
    )
    for index, line in enumerate(lines):
        match = pattern.search(line)
        if not match:
            continue
        end = _brace_end(lines, index)
        if end:
            definitions.setdefault(match.group(1), []).append((index + 1, end))
    return definitions


def _one_hop_ranges(lines, start, end):
    if not start or not end:
        return []
    text = "\n".join(lines[start - 1 : end])
    calls = {
        match.group(1)
        for match in re.finditer(
            r"\b(?:this\.)?([A-Za-z_$][A-Za-z0-9_$]*)\s*\(", text
        )
    }
    excluded = {
        "if",
        "for",
        "while",
        "switch",
        "catch",
        "log",
        "error",
        "warn",
        "save",
        "update",
        "delete",
        "set",
        "get",
    }
    definitions = _method_definitions(lines)
    ranges = []
    for name in sorted(calls - excluded):
        targets = definitions.get(name) or []
        if len(targets) == 1 and not (start <= targets[0][0] <= end):
            ranges.append(targets[0])
    return ranges


def _source_ref(file_path, line, lines, rule_id):
    if not file_path or line < 1 or line > len(lines):
        return None
    return {
        "source_type": "source",
        "file": file_path.replace("\\", "/"),
        "start_line": line,
        "end_line": line,
        "rule_id": rule_id,
        "snippet": lines[line - 1].strip()[:500],
    }


def _find_guard(file_path, lines, ranges):
    indexed = []
    for start, end in ranges:
        indexed.extend((line, lines[line - 1]) for line in range(start, end + 1))
    text = "\n".join(value for _, value in indexed)
    lowered = text.lower()
    patterns = [
        (
            "redis_atomic_guard_observed",
            re.compile(
                r"\bsetnx\s*\(|\.set\s*\([^;\n]*(?:[\"']NX[\"']|\bNX\s*:\s*true)",
                re.I,
            ),
        ),
        (
            "inbox_or_processed_event_observed",
            re.compile(
                r"\b(?:processed[_A-Za-z]*(?:event|message|job)|"
                r"consumed[_A-Za-z]*(?:event|message)|inbox)(?:s|es)?\b"
                r"[\s\S]{0,300}\b(?:insert|save|upsert|persist)\s*\(",
                re.I,
            ),
        ),
        (
            "persistent_guard_observed",
            re.compile(
                r"\b(?:idempotency|dedup(?:e|lication)?)[A-Za-z0-9_$.]*"
                r"\.(?:claim|acquire|checkAndSet|reserve|record|store|executeOnce)\s*\(",
                re.I,
            ),
        ),
        (
            "unique_constraint_observed",
            re.compile(
                r"(?:@Unique\b|unique\s*:\s*true|\bUNIQUE\b|"
                r"\bon\s+conflict\b|\binsert\s+ignore\b)",
                re.I,
            ),
        ),
    ]
    for status, pattern in patterns:
        match = pattern.search(text)
        if not match:
            continue
        prefix = text[: match.start()]
        line_offset = prefix.count("\n")
        line = indexed[min(line_offset, len(indexed) - 1)][0]
        ref = _source_ref(file_path, line, lines, "consumer_idempotency_guard")
        return status, [ref] if ref else [], []
    has_check = bool(
        re.search(r"\b(?:exists|existsBy|findOne|findById|alreadyProcessed)\w*\s*\(", text)
    )
    has_write = bool(
        re.search(r"\b(?:save|insert|update|upsert|persist)\s*\(", text)
    )
    has_identity = any(
        token in lowered
        for token in ("messageid", "message_id", "eventid", "event_id", "job.id", "jobid")
    )
    if has_check and has_write and has_identity:
        line = next(
            (
                line_no
                for line_no, value in indexed
                if re.search(r"\b(?:exists|findOne|findById|alreadyProcessed)", value)
            ),
            indexed[0][0],
        )
        ref = _source_ref(file_path, line, lines, "consumer_guard_signal")
        return (
            "guard_signal_observed",
            [ref] if ref else [],
            ["check_then_write_atomicity_unresolved"],
        )
    return "none_observed", [], []


def _event_effects(event_facts, file_path, ranges, consumer_event_id):
    effects = []
    for fact in event_facts:
        if fact.get("event_id") == consumer_event_id:
            continue
        if fact.get("kind") not in SIDE_EFFECT_KINDS:
            continue
        ref = fact.get("ref") or {}
        if str(ref.get("file") or "") != file_path:
            continue
        line = int(ref.get("start_line") or 0)
        if not any(start <= line <= end for start, end in ranges):
            continue
        effects.append(
            {
                "event_id": str(fact.get("event_id") or ""),
                "kind": str(fact.get("kind") or ""),
                "file": file_path,
                "line_start": line,
                "evidence_refs": [ref],
            }
        )
    effects.sort(
        key=lambda item: (
            item["file"],
            item["line_start"],
            item["kind"],
            item["event_id"],
        )
    )
    return effects


def analyze_consumer_idempotency(repo_root, consumers, event_facts):
    root = Path(repo_root)
    cache = {}
    output = {}
    for consumer in consumers:
        ref = consumer.get("ref") or {}
        file_path = str(ref.get("file") or "")
        event_id = str(consumer.get("event_id") or "")
        if not file_path:
            continue
        if file_path not in cache:
            try:
                cache[file_path] = (root / file_path).read_text(
                    encoding="utf-8"
                ).splitlines()
            except (OSError, UnicodeDecodeError):
                cache[file_path] = []
        lines = cache[file_path]
        if not lines:
            output[event_id] = {
                "consumer_idempotency_status": "unknown",
                "consumer_side_effects": [],
                "guard_evidence_refs": [],
                "handler_refs": [],
                "limitations": ["consumer_source_unavailable"],
            }
            continue
        anchor = int(ref.get("start_line") or 0)
        framework = str(consumer.get("framework") or "")
        if framework in {"spring_kafka", "spring_rabbit"}:
            start, end = _java_handler_range(lines, anchor)
        else:
            start, end = _typescript_method_range(
                lines,
                anchor,
                str((consumer.get("meta") or {}).get("consumer_style") or ""),
            )
        if not start or not end:
            output[event_id] = {
                "consumer_idempotency_status": "unknown",
                "consumer_side_effects": [],
                "guard_evidence_refs": [],
                "handler_refs": [ref],
                "limitations": ["consumer_handler_scope_unresolved"],
            }
            continue
        ranges = [(start, end)] + _one_hop_ranges(lines, start, end)
        status, guard_refs, limitations = _find_guard(
            file_path, lines, ranges
        )
        effects = _event_effects(
            event_facts, file_path, ranges, event_id
        )
        handler_ref = _source_ref(
            file_path, start, lines, "queue_consumer_handler"
        )
        output[event_id] = {
            "consumer_idempotency_status": (
                status if effects else "unknown"
            ),
            "consumer_side_effects": effects,
            "guard_evidence_refs": guard_refs,
            "handler_refs": [handler_ref] if handler_ref else [ref],
            "limitations": limitations,
            "handler_range": {"start_line": start, "end_line": end},
        }
    return output
