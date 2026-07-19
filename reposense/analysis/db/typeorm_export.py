import json
from pathlib import Path

from ...evidence.location import canonicalize_evidence_ref
from .typeorm_schema import normalize_operation, stable_operation_id
from .typeorm_summary import summarize_typeorm_operations


def _read_json(path, default):
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return default


def _node_evidence(run_root, node, repo_root):
    refs = []
    for evidence_id in node.get("evidence") or []:
        raw = _read_json(run_root / "evidence" / f"{evidence_id}.json", {})
        canonical = canonicalize_evidence_ref(
            raw,
            repo_root=repo_root,
            allow_repo_absolute=True,
        )
        if canonical is not None:
            canonical["event_id"] = node.get("event_id")
            refs.append(canonical)
    return refs


def build_typeorm_db_operations(run_dir):
    run_root = Path(run_dir)
    graph = _read_json(run_root / "event_graph.json", {"nodes": []})
    manifest = _read_json(run_root / "manifest.json", {})
    repo_root = str(manifest.get("repo_root") or "")
    operations = []
    seen = set()
    for node in graph.get("nodes") or []:
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        if str(meta.get("framework") or "").lower() != "typeorm":
            continue
        node_type = str(node.get("type") or "")
        if node_type not in {"db_op", "tx_boundary"}:
            continue
        evidence_refs = _node_evidence(run_root, node, repo_root)
        if not evidence_refs:
            continue
        ref = evidence_refs[0]
        item = {
            "kind": (
                "db.transaction"
                if node_type == "tx_boundary"
                else str(meta.get("db.kind") or "db.query_unknown")
            ),
            "operation": str(
                meta.get("db.op")
                or meta.get("transaction_style")
                or meta.get("tx.kind")
                or ""
            ),
            "receiver_kind": str(meta.get("receiver_kind") or "unknown"),
            "receiver_name": str(meta.get("receiver_name") or meta.get("callee_expr") or ""),
            "entity": str(meta.get("entity_hint") or ""),
            "file": ref["file"],
            "line_start": ref["start_line"],
            "line_end": ref["end_line"],
            "scope": meta.get("scope") if isinstance(meta.get("scope"), dict) else {},
            "transaction_context": str(meta.get("transaction_context") or "unknown"),
            "confidence": float(node.get("confidence") or 0.0),
            "evidence_refs": evidence_refs,
            "signals": meta.get("signals") if isinstance(meta.get("signals"), list) else [],
            "limitations": meta.get("limitations") if isinstance(meta.get("limitations"), list) else [],
        }
        item["operation_id"] = stable_operation_id(item)
        normalized = normalize_operation(item)
        key = (
            normalized["file"],
            normalized["line_start"],
            normalized["receiver_name"],
            normalized["operation"],
            normalized["kind"],
        )
        if key in seen:
            continue
        seen.add(key)
        operations.append(normalized)
    operations.sort(
        key=lambda item: (
            item["file"],
            item["line_start"],
            item["kind"],
            item["receiver_name"],
            item["operation"],
        )
    )
    summary = summarize_typeorm_operations(operations)
    return {
        "version": "typeorm_db_operations_v1",
        "framework": "typeorm",
        "operations": operations,
        "limitations": list(summary["limitations"]),
    }, summary


def export_typeorm_db_operations(run_dir):
    run_root = Path(run_dir)
    operations, summary = build_typeorm_db_operations(run_root)
    operations_path = run_root / "typeorm_db_operations.json"
    summary_path = run_root / "typeorm_db_summary.json"
    with operations_path.open("w", encoding="utf-8") as handle:
        json.dump(operations, handle, ensure_ascii=False)
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False)
    return {
        "operations": operations,
        "summary": summary,
        "operations_path": str(operations_path),
        "summary_path": str(summary_path),
    }
