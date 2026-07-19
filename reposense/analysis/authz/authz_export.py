import json
import os

from .authz_render import render_human_permission_review, render_negative_test_plan, render_permission_risk_report
from .authz_scanner import scan_permission_auditor
from .authz_summary import summarize_permission
from .guard_correlation_export import export_guard_correlation


def _write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def _write_text(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _repo_from_run(run_dir):
    for rel in ["run_manifest.json", "coverage.json", "report.json"]:
        obj = _read_json(os.path.join(run_dir, rel), {})
        candidates = [
            obj.get("repo_path") if isinstance(obj, dict) else None,
            (obj.get("meta") or {}).get("repo_path") if isinstance(obj, dict) else None,
            (obj.get("run_summary") or {}).get("repo_path") if isinstance(obj, dict) else None,
            (obj.get("stats") or {}).get("repo_path") if isinstance(obj, dict) else None,
        ]
        for c in candidates:
            if c and os.path.isdir(str(c)):
                return str(c)
    return None


def export_permission_auditor(run_dir, repo_path=None):
    repo = repo_path or _repo_from_run(run_dir)
    if not repo:
        raise ValueError("repo_path is required when run artifacts do not record a readable repository path")
    if not os.path.isdir(repo):
        raise ValueError("repo_path must be an existing directory")
    guard_result = export_guard_correlation(run_dir, repo, update_manifest=False)
    surface, risks_payload = scan_permission_auditor(
        run_dir,
        repo,
        guard_payload=guard_result["correlations"],
        guard_summary=guard_result["summary"],
    )
    summary = summarize_permission(surface, risks_payload.get("risks") or [])
    report_md = render_permission_risk_report(surface, risks_payload, summary)
    human_md = render_human_permission_review(risks_payload)
    test_plan_md = render_negative_test_plan(risks_payload)
    paths = {
        "surface_path": os.path.join(run_dir, "permission_surface.json"),
        "risks_path": os.path.join(run_dir, "permission_risks.json"),
        "report_path": os.path.join(run_dir, "permission_risk_report.md"),
        "human_review_path": os.path.join(run_dir, "human_permission_review_required.md"),
        "negative_test_plan_path": os.path.join(run_dir, "authz_negative_test_plan.md"),
    }
    _write_json(paths["surface_path"], surface)
    _write_json(paths["risks_path"], risks_payload)
    _write_text(paths["report_path"], report_md)
    _write_text(paths["human_review_path"], human_md)
    _write_text(paths["negative_test_plan_path"], test_plan_md)
    from ..context.context_export import export_review_context

    context_result = export_review_context(
        run_dir,
        repo,
        routes=surface.get("routes") or [],
        route_annotations=surface.get("route_intent_annotations") or [],
        update_manifest=False,
    )
    try:
        from ...run_manifest import build_run_manifest

        build_run_manifest(run_dir, write=True)
    except Exception:
        pass
    return {
        "surface": surface,
        "risks": risks_payload,
        "summary": summary,
        "report_markdown": report_md,
        "human_review_markdown": human_md,
        "negative_test_plan_markdown": test_plan_md,
        "review_context": context_result,
        "guard_correlation": guard_result,
        **paths,
    }
