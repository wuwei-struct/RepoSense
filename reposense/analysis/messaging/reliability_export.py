import json
import os
import shutil
from pathlib import Path

from .reliability_correlation import (
    correlate_queue_reliability,
    summarize_queue_reliability,
)


ARTIFACT_NAMES = [
    "queue_reliability_correlations.json",
    "queue_reliability_summary.json",
    "queue_reliability_risks.json",
]


def _read_json(path, default):
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return default


def _write_json(path, value):
    with Path(path).open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True)


def _repo_from_run(run_dir):
    manifest = _read_json(Path(run_dir) / "manifest.json", {})
    repo = str(manifest.get("repo_root") or "")
    return repo if repo and os.path.isdir(repo) else None


def _upsert_existing_context_pack(run_dir, summary):
    pack_root = Path(run_dir) / "context_pack"
    if not pack_root.is_dir():
        return
    artifacts = pack_root / "ARTIFACTS"
    artifacts.mkdir(parents=True, exist_ok=True)
    for name in ARTIFACT_NAMES:
        source = Path(run_dir) / name
        if source.is_file():
            shutil.copyfile(source, artifacts / name)
    index_path = pack_root / "MAP" / "index.json"
    index = _read_json(index_path, {})
    outputs = (
        index.get("outputs")
        if isinstance(index.get("outputs"), dict)
        else {}
    )
    for name in ARTIFACT_NAMES:
        if (artifacts / name).is_file():
            outputs[name.removesuffix(".json")] = (
                f"context_pack/ARTIFACTS/{name}"
            )
    index["outputs"] = outputs
    _write_json(index_path, index)
    readme_path = pack_root / "README.md"
    text = ""
    if readme_path.is_file():
        text = readme_path.read_text(encoding="utf-8")
    marker = "## Queue Reliability"
    if marker in text:
        text = text.split(marker, 1)[0].rstrip() + "\n\n"
    rows = [
        marker,
        f"- matched channels: {int(summary.get('matched_channels') or 0)}",
        f"- explicit retries: {int(summary.get('explicit_retries') or 0)}",
        (
            "- retry with guard / producer dedupe only / without guard: "
            f"{int(summary.get('retry_with_consumer_guard') or 0)} / "
            f"{int(summary.get('retry_with_producer_dedupe_only') or 0)} / "
            f"{int(summary.get('retry_without_consumer_guard') or 0)}"
        ),
        "- Producer identity does not prove consumer business idempotency.",
        (
            "- files: ARTIFACTS/queue_reliability_correlations.json, "
            "ARTIFACTS/queue_reliability_summary.json, "
            "ARTIFACTS/queue_reliability_risks.json"
        ),
    ]
    readme_path.write_text(
        (text + "\n".join(rows) + "\n").strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )


def export_queue_reliability(run_dir, repo_path=None, update_manifest=True):
    repo = repo_path or _repo_from_run(run_dir)
    if not repo:
        raise ValueError(
            "repo_path is required when run artifacts do not record a readable repository path"
        )
    correlations, risks = correlate_queue_reliability(run_dir, repo)
    summary = summarize_queue_reliability(correlations, risks)
    root = Path(run_dir)
    payloads = {
        "queue_reliability_correlations.json": {
            "version": "queue_reliability_correlations_v1",
            "correlations": correlations,
            "limitations": list(summary["limitations"]),
        },
        "queue_reliability_summary.json": summary,
        "queue_reliability_risks.json": {
            "version": "queue_reliability_risks_v1",
            "risks": risks,
            "limitations": list(summary["limitations"]),
        },
    }
    for name, payload in payloads.items():
        _write_json(root / name, payload)
    _upsert_existing_context_pack(root, summary)
    if update_manifest:
        try:
            from ...run_manifest import build_run_manifest

            build_run_manifest(str(root), write=True)
        except (OSError, ValueError):
            pass
    return {
        "correlations": payloads["queue_reliability_correlations.json"],
        "summary": summary,
        "risks": payloads["queue_reliability_risks.json"],
        "paths": {
            name: str(root / name) for name in ARTIFACT_NAMES
        },
    }
