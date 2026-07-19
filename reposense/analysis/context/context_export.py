import json
import os
from collections import Counter

from .file_context import classify_file_contexts
from .route_intent import classify_route_intents


LIMITATIONS = [
    "Context classification is deterministic and conservative.",
    "Public authentication intent does not prove that an endpoint is safe.",
    "Non-production file classification changes review priority, not the underlying fact.",
]


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return default


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)


def _summary(route_annotations, file_annotations, findings):
    route_counts = Counter(row.get("intent") for row in route_annotations)
    file_counts = Counter(row.get("context") for row in file_annotations)
    downweighted = 0
    excluded = 0
    for finding in findings:
        modifier = str((finding.get("metadata") or {}).get("review_modifier") or "normal")
        if modifier == "downweight":
            downweighted += 1
        elif modifier == "exclude_from_primary_review":
            excluded += 1
    return {
        "version": "review_context_summary_v1",
        "public_auth_route_count": int(route_counts.get("public_auth_entrypoint", 0)),
        "protected_auth_operation_count": int(route_counts.get("protected_auth_operation", 0)),
        "route_intent_conflict_count": len(
            [row for row in route_annotations if "route_intent_conflict" in (row.get("limitations") or [])]
        ),
        "generated_file_count": int(file_counts.get("generated", 0)),
        "seed_file_count": int(file_counts.get("seed", 0)),
        "template_file_count": int(file_counts.get("template", 0)),
        "fixture_file_count": int(file_counts.get("fixture", 0)),
        "test_file_count": int(file_counts.get("test", 0)),
        "findings_downweighted_count": downweighted,
        "findings_excluded_from_primary_review_count": excluded,
        "limitations": LIMITATIONS[:],
    }


def export_review_context(
    run_dir,
    repo_path,
    routes=None,
    route_annotations=None,
    file_annotations=None,
    findings=None,
    update_manifest=True,
):
    if routes is None:
        surface = _read_json(os.path.join(run_dir, "permission_surface.json"), {})
        routes = surface.get("routes") if isinstance(surface.get("routes"), list) else []
    if route_annotations is None:
        route_annotations, _ = classify_route_intents(routes, repo_path)
    if findings is None:
        health = _read_json(os.path.join(run_dir, "code_health.json"), {})
        findings = health.get("findings") if isinstance(health.get("findings"), list) else []
    if file_annotations is None:
        file_annotations = classify_file_contexts(
            repo_path,
            extra_paths=[row.get("file") for row in findings if isinstance(row, dict)],
        )

    route_payload = {
        "version": "route_intent_annotations_v1",
        "annotations": route_annotations,
        "limitations": LIMITATIONS[:],
    }
    file_payload = {
        "version": "file_context_annotations_v1",
        "annotations": file_annotations,
        "limitations": LIMITATIONS[:],
    }
    summary = _summary(route_annotations, file_annotations, findings)
    paths = {
        "route_intent_path": os.path.join(run_dir, "route_intent_annotations.json"),
        "file_context_path": os.path.join(run_dir, "file_context_annotations.json"),
        "review_context_summary_path": os.path.join(run_dir, "review_context_summary.json"),
    }
    _write_json(paths["route_intent_path"], route_payload)
    _write_json(paths["file_context_path"], file_payload)
    _write_json(paths["review_context_summary_path"], summary)
    if update_manifest:
        try:
            from ...run_manifest import build_run_manifest

            build_run_manifest(run_dir, write=True)
        except Exception:
            pass
    return {
        "route_intent_annotations": route_payload,
        "file_context_annotations": file_payload,
        "summary": summary,
        **paths,
    }
