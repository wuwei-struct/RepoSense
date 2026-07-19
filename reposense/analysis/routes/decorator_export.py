import json
import os

from .typescript_decorator_classifier import scan_typescript_decorators


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)


def export_route_decorator_classifications(
    run_dir,
    repo_path,
    update_manifest=True,
):
    result = scan_typescript_decorators(repo_path)
    payload = {
        "version": result["version"],
        "classifications": result["classifications"],
        "limitations": result["limitations"],
    }
    paths = {
        "classifications_path": os.path.join(
            run_dir,
            "route_decorator_classifications.json",
        ),
        "summary_path": os.path.join(run_dir, "route_decorator_summary.json"),
    }
    _write_json(paths["classifications_path"], payload)
    _write_json(paths["summary_path"], result["summary"])
    if update_manifest:
        try:
            from ...run_manifest import build_run_manifest

            build_run_manifest(run_dir, write=True)
        except Exception:
            pass
    return {
        "payload": payload,
        "summary": result["summary"],
        "routes": result["routes"],
        **paths,
    }
