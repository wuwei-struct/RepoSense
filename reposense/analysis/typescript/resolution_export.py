import json
from collections import Counter
from pathlib import Path

from .import_graph import build_typescript_index
from .wrapper_resolution import resolve_typeorm_wrappers


def _read_json(path, default):
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return default


def _write_json(path, value):
    with Path(path).open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True)


def export_typeorm_alias_resolution(run_dir, repo_path):
    run_root = Path(run_dir)
    index = build_typescript_index(repo_path)
    typeorm = _read_json(run_root / "typeorm_db_operations.json", {})
    operations = [
        item
        for item in typeorm.get("operations") or []
        if isinstance(item, dict) and item.get("kind") == "db.write"
    ]
    resolutions, duplicates = resolve_typeorm_wrappers(index, operations)
    counts = Counter(
        str(item.get("resolution_status") or "unresolved")
        for item in resolutions
    )
    limitations = sorted(
        {
            limitation
            for item in resolutions
            for limitation in (item.get("limitations") or [])
        }
    )
    artifact = {
        "version": "typeorm_alias_resolutions_v1",
        "resolutions": resolutions,
        "limitations": limitations,
    }
    summary = {
        "version": "typeorm_alias_resolution_summary_v1",
        "candidate_receivers": len(resolutions),
        "resolved_direct": counts["resolved_direct_import"],
        "resolved_alias": counts["resolved_alias_import"],
        "resolved_reexport": counts["resolved_reexport"],
        "resolved_barrel": counts["resolved_barrel"],
        "resolved_local_assignment": counts["resolved_local_assignment"],
        "ambiguous": counts["ambiguous"],
        "unresolved": counts["unresolved"],
        "depth_exceeded": sum(
            "cross_file_resolution_depth_exceeded"
            in (item.get("limitations") or [])
            for item in resolutions
        ),
        "duplicate_resolutions_removed": duplicates,
        "resolved_wrapper_calls": sum(
            str(item.get("resolution_status") or "").startswith("resolved_")
            and bool(item.get("db_operation_ids"))
            for item in resolutions
        ),
        "limitations": limitations,
    }
    paths = {
        "import_graph": run_root / "typescript_import_graph.json",
        "symbol_index": run_root / "typescript_symbol_index.json",
        "resolutions": run_root / "typeorm_alias_resolutions.json",
        "summary": run_root / "typeorm_alias_resolution_summary.json",
    }
    _write_json(paths["import_graph"], index["import_graph"])
    _write_json(paths["symbol_index"], index["symbol_index"])
    _write_json(paths["resolutions"], artifact)
    _write_json(paths["summary"], summary)
    return {
        "import_graph": index["import_graph"],
        "symbol_index": index["symbol_index"],
        "resolutions": artifact,
        "summary": summary,
        "paths": {key: str(value) for key, value in paths.items()},
    }
