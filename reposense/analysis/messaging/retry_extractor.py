import os
import re
from pathlib import Path


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


def _balanced_text(lines, start_line, max_lines=40):
    start = max(0, int(start_line or 1) - 1)
    chosen = []
    parens = braces = brackets = 0
    seen = False
    quote = ""
    escaped = False
    for line in lines[start : start + max_lines]:
        chosen.append(line)
        for char in line:
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
                continue
            if char == "(":
                parens += 1
                seen = True
            elif char == ")":
                parens -= 1
            elif char == "{":
                braces += 1
            elif char == "}":
                braces -= 1
            elif char == "[":
                brackets += 1
            elif char == "]":
                brackets -= 1
        if seen and parens <= 0 and braces <= 0 and brackets <= 0:
            break
    return "\n".join(chosen)


def _numeric_option(text, name):
    match = re.search(
        rf"\b{re.escape(name)}\s*[:=]\s*[\"']?([A-Za-z0-9_.$(){{}}+-]+)",
        text,
    )
    if not match:
        return None, ""
    expression = match.group(1).strip("\"'")
    return (int(expression), expression) if expression.isdigit() else (None, expression)


def _option_line(text, start_line, name):
    for offset, value in enumerate(text.splitlines()):
        if re.search(rf"\b{re.escape(name)}\s*[:=]", value):
            return start_line + offset
    return start_line


def _backoff(text):
    match = re.search(r"\bbackoff\s*[:=]\s*([^,\n}]+|\{[^}]+\})", text)
    if not match:
        return {}
    raw = " ".join(match.group(1).split())
    kind = ""
    lowered = raw.lower()
    if "exponential" in lowered:
        kind = "exponential"
    elif "fixed" in lowered or raw.isdigit():
        kind = "fixed"
    return {"expression": raw[:300], "kind": kind or "configured"}


def _bull_default_options(lines, receiver):
    if not receiver:
        return "", 0
    receiver = receiver.split(".")[-1]
    pattern = re.compile(
        rf"\b(?:const|let|var|private|protected|public|readonly|\s)*"
        rf"{re.escape(receiver)}\b[^=\n]*=\s*new\s+(?:Queue|BullQueue)\b"
    )
    for index, line in enumerate(lines):
        if not pattern.search(line):
            continue
        block = _balanced_text(lines, index + 1, 50)
        if "defaultJobOptions" in block:
            return block, index + 1
    return "", 0


def _stable_job_id(text):
    match = re.search(r"\bjobId\s*:\s*([^,\n}]+)", text)
    if not match:
        return False, ""
    expression = match.group(1).strip()
    lowered = expression.lower()
    unstable = any(
        token in lowered
        for token in ("random", "uuid(", "nanoid(", "date.now", "timestamp")
    )
    identity_like = bool(
        re.search(r"\b(id|key|message|event|order|job)\b", lowered)
        or re.match(r"[\"'][^\"']+[\"']", expression)
    )
    return bool(identity_like and not unstable), expression[:300]


def _bull_signal(fact, lines):
    ref = fact.get("ref") or {}
    line = int(ref.get("start_line") or 0)
    call = _balanced_text(lines, line)
    meta = fact.get("meta") or {}
    receiver = str(meta.get("callee_expr") or "").rsplit(".", 1)[0]
    defaults, default_line = _bull_default_options(lines, receiver)
    source = call
    source_line = line
    source_kind = "add_options"
    if "attempts" not in call and defaults:
        source = defaults
        source_line = default_line
        source_kind = "default_job_options"
    attempts, attempts_expr = _numeric_option(source, "attempts")
    if attempts is not None:
        retry_status = "explicit_retry" if attempts > 1 else "explicit_no_retry"
    elif attempts_expr:
        retry_status = "dynamic_or_unresolved"
    else:
        retry_status = "framework_default_or_unknown"
    evidence = []
    if attempts_expr:
        retry_ref = _source_ref(
            str(ref.get("file") or ""),
            _option_line(source, source_line, "attempts"),
            lines,
            "queue_retry_configuration",
        )
        if retry_ref:
            evidence.append(retry_ref)
    stable_job_id, job_id_expr = _stable_job_id(call)
    if "deduplication" in call:
        identity = "deduplication_option"
    elif stable_job_id:
        identity = "stable_job_id"
    elif "jobId" in call:
        identity = "unknown"
    else:
        identity = "none_observed"
    if identity not in {"none_observed", "unknown"}:
        identity_ref = _source_ref(
            str(ref.get("file") or ""),
            line,
            lines,
            "queue_producer_identity",
        )
        if identity_ref:
            evidence.append(identity_ref)
    return {
        "retry_status": retry_status,
        "retry_policy": {
            "attempts": attempts,
            "attempts_expression": attempts_expr,
            "backoff": _backoff(source),
            "source": source_kind if attempts_expr else "",
        },
        "producer_identity_status": identity,
        "identity_expression": job_id_expr,
        "evidence_refs": evidence,
        "limitations": (
            ["retry_configuration_dynamic"]
            if retry_status == "dynamic_or_unresolved"
            else []
        ),
    }


def _annotation_window(lines, line):
    start = max(0, line - 12)
    end = min(len(lines), line + 4)
    return "\n".join(lines[start:end]), start + 1


def _java_consumer_signal(fact, lines):
    ref = fact.get("ref") or {}
    line = int(ref.get("start_line") or 0)
    text, first_line = _annotation_window(lines, line)
    framework = str(fact.get("framework") or "")
    if framework == "spring_kafka":
        marker_pattern = re.compile(
            r"@RetryableTopic\b\s*(?:\((.*?)\))?", re.S
        )
        rule = "kafka_retry_configuration"
    else:
        marker_pattern = re.compile(
            r"@Retryable\b\s*(?:\((.*?)\))?", re.S
        )
        rule = "rabbit_retry_configuration"
    markers = list(marker_pattern.finditer(text))
    marker = markers[-1] if markers else None
    if not marker:
        return {
            "retry_status": "framework_default_or_unknown",
            "retry_policy": {},
            "evidence_refs": [],
            "limitations": [],
        }
    body = marker.group(1) or ""
    attempts, attempts_expr = _numeric_option(body, "attempts")
    if attempts is None:
        max_attempts, max_expr = _numeric_option(body, "maxAttempts")
        attempts, attempts_expr = max_attempts, max_expr or attempts_expr
    if attempts is not None:
        status = "explicit_retry" if attempts > 1 else "explicit_no_retry"
    elif attempts_expr:
        status = "dynamic_or_unresolved"
    else:
        status = "explicit_retry"
    annotation_line = first_line + text[: marker.start()].count("\n")
    evidence = _source_ref(str(ref.get("file") or ""), annotation_line, lines, rule)
    return {
        "retry_status": status,
        "retry_policy": {
            "attempts": attempts,
            "attempts_expression": attempts_expr,
            "backoff": _backoff(body),
            "source": marker.group(0).split("(", 1)[0],
        },
        "evidence_refs": [evidence] if evidence else [],
        "limitations": (
            ["retry_configuration_dynamic"]
            if status == "dynamic_or_unresolved"
            else []
        ),
    }


def _split_arguments(text):
    start = text.find("(")
    end = text.rfind(")")
    if start < 0 or end <= start:
        return []
    args = []
    current = []
    depth = 0
    quote = ""
    for char in text[start + 1 : end]:
        if quote:
            current.append(char)
            if char == quote:
                quote = ""
            continue
        if char in "\"'":
            quote = char
            current.append(char)
        elif char in "([{":
            depth += 1
            current.append(char)
        elif char in ")]}":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            args.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        args.append("".join(current).strip())
    return args


def _java_producer_identity(fact, lines, transport_idempotence_refs):
    ref = fact.get("ref") or {}
    line = int(ref.get("start_line") or 0)
    framework = str(fact.get("framework") or "")
    text = _balanced_text(lines, line, 12)
    status = "none_observed"
    if framework == "spring_kafka":
        args = _split_arguments(text)
        if "ProducerRecord" in text or len(args) >= 3:
            status = "message_key_observed"
        if transport_idempotence_refs:
            status = "transport_idempotence_observed"
    evidence = []
    if status != "none_observed":
        identity_ref = _source_ref(
            str(ref.get("file") or ""),
            line,
            lines,
            "queue_producer_identity",
        )
        if identity_ref:
            evidence.append(identity_ref)
    if status == "transport_idempotence_observed":
        evidence.extend(transport_idempotence_refs)
    return {
        "producer_identity_status": status,
        "evidence_refs": evidence,
        "limitations": (
            ["producer_transport_idempotence_is_not_consumer_idempotency"]
            if status == "transport_idempotence_observed"
            else []
        ),
    }


def scan_global_retry_configuration(repo_root):
    result = {
        "spring_kafka": [],
        "spring_rabbit": [],
        "transport_idempotence": False,
        "transport_idempotence_refs": [],
    }
    root = Path(repo_root)
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {
            ".java",
            ".kt",
            ".properties",
            ".yml",
            ".yaml",
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.relative_to(root).as_posix()
        lines = text.splitlines()
        for index, line in enumerate(lines, 1):
            lowered = line.lower().replace(" ", "")
            if (
                "enable.idempotence=true" in lowered
                or re.search(
                    r"""["']enable\.idempotence["']\s*[,=:]\s*true\b""",
                    line,
                    re.I,
                )
                or "enable_idempotence_config" in lowered
                and re.search(r"\btrue\b", lowered)
            ):
                result["transport_idempotence"] = True
                ref = _source_ref(
                    rel, index, lines, "kafka_transport_idempotence"
                )
                if ref:
                    result["transport_idempotence_refs"].append(ref)
            if "DefaultErrorHandler" in line and (
                "FixedBackOff" in text or "ExponentialBackOff" in text
            ):
                ref = _source_ref(rel, index, lines, "kafka_retry_configuration")
                if ref:
                    result["spring_kafka"].append(ref)
            if (
                "RetryInterceptorBuilder" in line
                or "RetryTemplate" in line
            ) and "setAdviceChain" in text:
                ref = _source_ref(rel, index, lines, "rabbit_retry_configuration")
                if ref:
                    result["spring_rabbit"].append(ref)
    return result


def extract_retry_signals(repo_root, facts):
    root = Path(repo_root)
    cache = {}
    global_config = scan_global_retry_configuration(root)
    signals = {}
    for fact in facts:
        ref = fact.get("ref") or {}
        rel = str(ref.get("file") or "")
        if not rel:
            continue
        if rel not in cache:
            try:
                cache[rel] = (root / rel).read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                cache[rel] = []
        lines = cache[rel]
        if not lines:
            continue
        framework = str(fact.get("framework") or "")
        role = fact.get("role")
        if role == "producer" and framework in {"bull", "bullmq"}:
            signal = _bull_signal(fact, lines)
        elif role == "consumer" and framework in {
            "spring_kafka",
            "spring_rabbit",
        }:
            signal = _java_consumer_signal(fact, lines)
        elif role == "producer" and framework in {
            "spring_kafka",
            "spring_rabbit",
        }:
            signal = _java_producer_identity(
                fact,
                lines,
                global_config["transport_idempotence_refs"],
            )
        else:
            signal = {}
        signals[str(fact.get("event_id") or "")] = signal
    return signals, global_config
