import json
from collections import Counter
from pathlib import Path

from .correlation_schema import stable_sort_correlations
from .spring_transaction_correlation import correlate_spring_transactions
from .typescript_transaction_correlation import (
    correlate_typescript_transactions,
)


def _write_json(path, value):
    with Path(path).open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True)


def export_transaction_correlations(run_dir, repo_path):
    java_artifact, java_summary = correlate_spring_transactions(
        run_dir, repo_path
    )
    typescript_artifact, typescript_summary = (
        correlate_typescript_transactions(run_dir, repo_path)
    )
    rows = stable_sort_correlations(
        list(java_artifact.get("correlations") or [])
        + list(typescript_artifact.get("correlations") or [])
    )
    coverage = Counter(
        str(item.get("coverage_status") or "unknown") for item in rows
    )
    language_framework = {
        "java/spring": java_summary,
        "typescript/typeorm": typescript_summary,
    }
    active = [
        (language, framework)
        for language, framework, artifact in [
            ("java", "spring", java_artifact),
            ("typescript", "typeorm", typescript_artifact),
        ]
        if artifact.get("correlations")
    ]
    correlations = {
        "version": "transaction_correlations_v1",
        "language": active[0][0] if len(active) == 1 else "multi",
        "framework": active[0][1] if len(active) == 1 else "multi",
        "languages": sorted({language for language, _ in active}),
        "frameworks": sorted({framework for _, framework in active}),
        "correlations": rows,
        "limitations": sorted(
            set(
                list(java_artifact.get("limitations") or [])
                + list(typescript_artifact.get("limitations") or [])
            )
        ),
    }
    summary = {
        "version": "transaction_correlation_summary_v1",
        "total_correlations": len(rows),
        "db_writes_considered": int(
            java_summary.get("db_writes_considered") or 0
        )
        + int(typescript_summary.get("db_writes_considered") or 0),
        "counts_by_coverage_status": {
            key: int(coverage.get(key, 0))
            for key in [
                "covered_explicit",
                "uncovered",
                "partially_covered",
                "read_only_transaction",
                "unknown",
            ]
        },
        "by_language_framework": language_framework,
        "explicit_covered_call_count": int(
            java_summary.get("explicit_covered_call_count") or 0
        ),
        "uncovered_call_count": int(
            java_summary.get("uncovered_call_count") or 0
        ),
        "read_only_write_call_count": int(
            java_summary.get("read_only_write_call_count") or 0
        ),
        "limitations": list(correlations["limitations"]),
    }
    run_root = Path(run_dir)
    correlations_path = run_root / "transaction_correlations.json"
    summary_path = run_root / "transaction_correlation_summary.json"
    _write_json(correlations_path, correlations)
    _write_json(summary_path, summary)
    return {
        "correlations": correlations,
        "summary": summary,
        "correlations_path": str(correlations_path),
        "summary_path": str(summary_path),
    }
