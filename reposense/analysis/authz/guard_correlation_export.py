import json
import os

from ..routes.decorator_export import export_route_decorator_classifications
from .route_guard_correlation import build_route_guard_correlation


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)


def export_guard_correlation(run_dir, repo_path, update_manifest=True):
    decorator_result = export_route_decorator_classifications(
        run_dir,
        repo_path,
        update_manifest=False,
    )
    correlations, summary, openapi, nest = build_route_guard_correlation(repo_path)
    paths = {
        "correlations_path": os.path.join(run_dir, "route_guard_correlations.json"),
        "summary_path": os.path.join(run_dir, "route_guard_summary.json"),
        "openapi_security_path": os.path.join(run_dir, "openapi_security_surface.json"),
    }
    _write_json(paths["correlations_path"], correlations)
    _write_json(paths["summary_path"], summary)
    _write_json(paths["openapi_security_path"], openapi)
    if update_manifest:
        try:
            from ...run_manifest import build_run_manifest

            build_run_manifest(run_dir, write=True)
        except Exception:
            pass
    return {
        "correlations": correlations,
        "summary": summary,
        "openapi_security_surface": openapi,
        "nestjs_guard_surface": nest,
        "route_decorator_classification": decorator_result,
        **paths,
    }
