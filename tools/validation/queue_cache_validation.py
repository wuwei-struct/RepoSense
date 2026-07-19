#!/usr/bin/env python3
"""Validate queue/cache facts without executing the analyzed repository."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from reposense.evidence.location import canonicalize_evidence_ref
from reposense.evidence.validation import validate_evidence_location


MATCH_STATUSES = {
    "matched",
    "dispatch_only",
    "consume_only",
    "unknown_name",
    "ambiguous",
}
QUEUE_OPERATIONS = {"queue.dispatch", "queue.consume"}
CACHE_OPERATIONS = {"cache.read", "cache.write", "cache.invalidate"}


def _read_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n")


def _stable_id(*parts: Any) -> str:
    material = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(material.encode("utf-8")).hexdigest()[:16]


def _event_operation(node: dict[str, Any]) -> str:
    event_type = str(node.get("type") or "")
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    if event_type == "queue_dispatch":
        return "queue.dispatch"
    if event_type == "queue_consume":
        return "queue.consume"
    if event_type == "cache_op":
        return str(meta.get("cache.kind") or "")
    return ""


def _event_evidence(
    run_dir: Path,
    repo_root: Path,
    node: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    refs: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    event_id = str(node.get("event_id") or "")
    for evidence_id in node.get("evidence") if isinstance(node.get("evidence"), list) else []:
        evidence_path = run_dir / "evidence" / f"{evidence_id}.json"
        evidence = _read_json(evidence_path, {})
        canonical = canonicalize_evidence_ref(
            evidence,
            repo_root=repo_root,
            allow_repo_absolute=True,
        )
        if canonical is None:
            issues.extend(
                validate_evidence_location(
                    evidence,
                    repo_root,
                    artifact="event_graph.json",
                    item_id=f"{event_id}:{evidence_id}",
                    require_snippet=True,
                    allow_repo_absolute=True,
                )
            )
            continue
        canonical["source_type"] = "event"
        canonical["event_id"] = event_id
        canonical["evidence_id"] = str(evidence_id)
        refs.append(canonical)
        issues.extend(
            validate_evidence_location(
                canonical,
                repo_root,
                artifact="queue_cache_validation.json",
                item_id=event_id,
                require_snippet=True,
            )
        )
    return refs, issues


def _base_observation(
    node: dict[str, Any],
    operation: str,
    evidence_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    primary = evidence_refs[0] if evidence_refs else {}
    return {
        "event_id": str(node.get("event_id") or ""),
        "operation": operation,
        "framework": str(
            meta.get("framework")
            or meta.get("queue.system")
            or meta.get("cache.backend")
            or "unknown"
        ),
        "file": str(primary.get("file") or meta.get("path") or ""),
        "line": int(primary.get("start_line") or 0),
        "evidence_refs": evidence_refs,
        "confidence": float(node.get("confidence") or 0.0),
        "limitations": [],
    }


def _queue_observation(
    node: dict[str, Any],
    operation: str,
    evidence_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    item = _base_observation(node, operation, evidence_refs)
    name = str(meta.get("queue_name") or meta.get("topic_name") or "").strip()
    expression = str(
        meta.get("queue_name_expr")
        or meta.get("topic_name_expr")
        or ""
    ).strip()
    resolved = bool(meta.get("queue_name_resolved")) and bool(name)
    item.update(
        {
            "queue_name": name,
            "queue_name_expression": expression,
            "queue_name_resolved": resolved,
            "producer_consumer": (
                "producer" if operation == "queue.dispatch" else "consumer"
            ),
            "match_status": "unknown_name",
        }
    )
    if not resolved:
        item["limitations"].append("queue_name_unresolved")
    return item


def _cache_observation(
    node: dict[str, Any],
    operation: str,
    evidence_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    item = _base_observation(node, operation, evidence_refs)
    key_literal = str(meta.get("key_literal") or "").strip()
    key_expression = str(meta.get("key_expr") or "").strip()
    item.update(
        {
            "client_kind": str(
                meta.get("cache.backend")
                or meta.get("framework")
                or "unknown"
            ),
            "key_expression": key_expression or key_literal,
            "key_resolved": bool(meta.get("key_resolved")) and bool(key_literal),
            "receiver_source": str(meta.get("receiver_source") or ""),
        }
    )
    if not item["key_resolved"]:
        item["limitations"].append("cache_key_unresolved")
    return item


def _queue_identity(item: dict[str, Any]) -> tuple[str, str] | None:
    if not item.get("queue_name_resolved"):
        return None
    framework = str(item.get("framework") or "unknown").strip().lower()
    name = str(item.get("queue_name") or "").strip()
    return (framework, name) if name else None


def _deduplicate(
    items: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    duplicates = 0
    for item in items:
        key = (
            item.get("operation"),
            item.get("framework"),
            item.get("file"),
            item.get("line"),
            item.get("queue_name"),
            item.get("queue_name_expression"),
            item.get("key_expression"),
        )
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique.append(item)
    return unique, duplicates


def _match_queues(
    observations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[
        tuple[str, str],
        dict[str, list[dict[str, Any]]],
    ] = defaultdict(lambda: {"dispatch": [], "consume": []})
    for item in observations:
        identity = _queue_identity(item)
        if identity is None:
            item["match_status"] = "unknown_name"
            continue
        side = "dispatch" if item["operation"] == "queue.dispatch" else "consume"
        grouped[identity][side].append(item)

    pairs: list[dict[str, Any]] = []
    for (framework, name), sides in sorted(grouped.items()):
        dispatches = sides["dispatch"]
        consumers = sides["consume"]
        if dispatches and consumers:
            status = "matched"
        elif dispatches:
            status = "dispatch_only"
        else:
            status = "consume_only"
        for item in dispatches + consumers:
            item["match_status"] = status
        pairs.append(
            {
                "pair_id": _stable_id(framework, name),
                "framework": framework,
                "queue_name": name,
                "match_status": status,
                "dispatch_event_ids": sorted(
                    str(item["event_id"]) for item in dispatches
                ),
                "consumer_event_ids": sorted(
                    str(item["event_id"]) for item in consumers
                ),
            }
        )
    return pairs


def build_validation(
    run_dir: str | Path,
    repo_path: str | Path,
    *,
    case_id: str = "",
    commit_sha: str = "",
) -> dict[str, Any]:
    run_root = Path(run_dir).resolve()
    repo_root = Path(repo_path).resolve()
    graph = _read_json(run_root / "event_graph.json", {})
    nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []

    queue_observations: list[dict[str, Any]] = []
    cache_observations: list[dict[str, Any]] = []
    evidence_issues: list[dict[str, Any]] = []
    evidence_checked = 0
    for node in nodes:
        if not isinstance(node, dict):
            continue
        operation = _event_operation(node)
        if operation not in QUEUE_OPERATIONS | CACHE_OPERATIONS:
            continue
        refs, issues = _event_evidence(run_root, repo_root, node)
        evidence_checked += len(
            node.get("evidence")
            if isinstance(node.get("evidence"), list)
            else []
        )
        evidence_issues.extend(issues)
        if operation in QUEUE_OPERATIONS:
            queue_observations.append(
                _queue_observation(node, operation, refs)
            )
        else:
            cache_observations.append(
                _cache_observation(node, operation, refs)
            )

    queue_observations, queue_duplicates = _deduplicate(
        queue_observations
    )
    cache_observations, cache_duplicates = _deduplicate(
        cache_observations
    )
    matched_pairs = _match_queues(queue_observations)

    queue_observations.sort(
        key=lambda item: (
            item["framework"],
            item["queue_name"],
            item["file"],
            item["line"],
            item["operation"],
            item["event_id"],
        )
    )
    cache_observations.sort(
        key=lambda item: (
            item["client_kind"],
            item["file"],
            item["line"],
            item["operation"],
            item["event_id"],
        )
    )
    status_counts = Counter(
        item["match_status"] for item in queue_observations
    )
    cache_counts = Counter(
        item["operation"] for item in cache_observations
    )
    queue_names = sorted(
        {
            item["queue_name"]
            for item in queue_observations
            if item.get("queue_name_resolved")
        }
    )
    limitations = [
        "Queue/topic matching requires the same framework and a statically resolved name.",
        "Dynamic queue names and cache keys are retained as expressions and require human confirmation.",
        "Static observations do not prove runtime delivery, retry behavior, or cache consistency.",
    ]
    if evidence_issues:
        limitations.append("One or more queue/cache evidence locations failed validation.")

    return {
        "version": "queue_cache_validation_v1",
        "case_id": str(case_id or ""),
        "commit_sha": str(commit_sha or ""),
        "run_dir": "<RUN_DIR>",
        "summary": {
            "detected_frameworks": sorted(
                {
                    item["framework"]
                    for item in queue_observations
                }
            ),
            "queue_dispatch_count": sum(
                item["operation"] == "queue.dispatch"
                for item in queue_observations
            ),
            "queue_consume_count": sum(
                item["operation"] == "queue.consume"
                for item in queue_observations
            ),
            "queue_names": queue_names,
            "matched_producer_consumer_pairs": sum(
                pair["match_status"] == "matched"
                for pair in matched_pairs
            ),
            "unmatched_dispatches": status_counts["dispatch_only"],
            "unmatched_consumers": status_counts["consume_only"],
            "unknown_name_events": status_counts["unknown_name"],
            "cache_read_count": cache_counts["cache.read"],
            "cache_write_count": cache_counts["cache.write"],
            "cache_invalidate_count": cache_counts["cache.invalidate"],
            "cache_clients": sorted(
                {
                    item["client_kind"]
                    for item in cache_observations
                }
            ),
            "duplicate_event_count": queue_duplicates + cache_duplicates,
            "evidence_checked": evidence_checked,
            "evidence_valid": max(0, evidence_checked - len(evidence_issues)),
            "evidence_errors": len(evidence_issues),
        },
        "queue_observations": queue_observations,
        "cache_observations": cache_observations,
        "producer_consumer_pairs": matched_pairs,
        "evidence_issues": evidence_issues,
        "limitations": limitations,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Queue / Cache Validation",
        "",
        "This report validates static RepoSense queue/cache observations. It does not execute the target repository.",
        "",
        "## Summary",
        "",
        f"- Queue dispatches: {summary.get('queue_dispatch_count', 0)}",
        f"- Queue consumers: {summary.get('queue_consume_count', 0)}",
        f"- Matched producer/consumer pairs: {summary.get('matched_producer_consumer_pairs', 0)}",
        f"- Unmatched dispatches: {summary.get('unmatched_dispatches', 0)}",
        f"- Unmatched consumers: {summary.get('unmatched_consumers', 0)}",
        f"- Unresolved queue names: {summary.get('unknown_name_events', 0)}",
        f"- Cache reads/writes/invalidations: {summary.get('cache_read_count', 0)}/{summary.get('cache_write_count', 0)}/{summary.get('cache_invalidate_count', 0)}",
        f"- Evidence checked/valid/errors: {summary.get('evidence_checked', 0)}/{summary.get('evidence_valid', 0)}/{summary.get('evidence_errors', 0)}",
        "",
        "## Producer / Consumer Pairs",
        "",
    ]
    pairs = payload.get("producer_consumer_pairs") or []
    if pairs:
        for pair in pairs:
            lines.append(
                f"- `{pair['framework']}:{pair['queue_name']}`: {pair['match_status']} "
                f"({len(pair['dispatch_event_ids'])} dispatch, {len(pair['consumer_event_ids'])} consume)"
            )
    else:
        lines.append("- No statically resolved producer/consumer pairs observed.")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in payload.get("limitations") or [])
    return "\n".join(lines) + "\n"


def build_triage_template(payload: dict[str, Any]) -> dict[str, Any]:
    selected: list[dict[str, Any]] = []
    queue_items = payload.get("queue_observations") or []
    cache_items = payload.get("cache_observations") or []
    queue_sample = [
        item
        for item in queue_items
        if item.get("match_status") != "matched"
    ]
    queue_sample += [
        item
        for item in queue_items
        if item.get("match_status") == "matched"
    ][:6]
    for item in queue_sample + cache_items[:6]:
        selected.append(
            {
                "item_id": _stable_id(
                    item.get("event_id"),
                    item.get("operation"),
                ),
                "source_artifact": "queue_cache_validation.json",
                "event_id": item.get("event_id"),
                "operation": item.get("operation"),
                "framework": item.get("framework")
                or item.get("client_kind"),
                "file": item.get("file"),
                "line": item.get("line"),
                "reason": (
                    item.get("match_status")
                    or ", ".join(item.get("limitations") or [])
                    or "static queue/cache observation"
                ),
                "evidence": item.get("evidence_refs") or [],
                "triage_status": "unreviewed",
                "reviewer_note": "",
            }
        )
    return {
        "version": "queue_cache_triage_v1",
        "allowed_statuses": [
            "confirmed_by_source",
            "plausible",
            "likely_false_positive",
            "needs_context",
            "duplicate",
            "unsupported",
            "unreviewed",
        ],
        "items": selected,
    }


def write_validation(
    run_dir: str | Path,
    repo_path: str | Path,
    *,
    case_id: str = "",
    commit_sha: str = "",
    case_dir: str | Path | None = None,
) -> dict[str, Any]:
    run_root = Path(run_dir).resolve()
    payload = build_validation(
        run_root,
        repo_path,
        case_id=case_id,
        commit_sha=commit_sha,
    )
    markdown = render_markdown(payload)
    triage = build_triage_template(payload)
    _write_json(run_root / "queue_cache_validation.json", payload)
    _write_text(run_root / "queue_cache_validation.md", markdown)
    if case_dir:
        case_root = Path(case_dir).resolve()
        _write_json(case_root / "queue_cache_validation.json", payload)
        _write_text(case_root / "queue_cache_validation.md", markdown)
        _write_json(
            case_root / "queue_cache_triage_template.json",
            triage,
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate queue/cache event coverage for one RepoSense run."
    )
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--repo-path", required=True)
    parser.add_argument("--case-id", default="")
    parser.add_argument("--commit", default="")
    parser.add_argument("--case-dir")
    args = parser.parse_args(argv)
    payload = write_validation(
        args.run_dir,
        args.repo_path,
        case_id=args.case_id,
        commit_sha=args.commit,
        case_dir=args.case_dir,
    )
    print(json.dumps(payload["summary"], ensure_ascii=False))
    return 1 if payload["summary"]["evidence_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
