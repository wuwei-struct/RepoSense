import json
import os

from .review_engine import generate_repository_review
from .review_render import render_human_review_required_markdown, render_repository_review_markdown


def _write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def _write_text(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def export_repository_review_report(run_dir):
    report = generate_repository_review(run_dir)
    matrix = report.get("risk_matrix") or {}
    human_items = report.get("human_review_required") or []
    report_md = render_repository_review_markdown(report)
    human_md = render_human_review_required_markdown(human_items)
    paths = {
        "report_json_path": os.path.join(run_dir, "repository_review_report.json"),
        "report_markdown_path": os.path.join(run_dir, "repository_review_report.md"),
        "risk_matrix_path": os.path.join(run_dir, "review_risk_matrix.json"),
        "human_review_path": os.path.join(run_dir, "human_review_required.md"),
    }
    _write_json(paths["report_json_path"], report)
    _write_text(paths["report_markdown_path"], report_md)
    _write_json(paths["risk_matrix_path"], matrix)
    _write_text(paths["human_review_path"], human_md)
    try:
        from ...run_manifest import build_run_manifest

        build_run_manifest(run_dir, write=True)
    except Exception:
        pass
    return {
        "report": report,
        "risk_matrix": matrix,
        "human_review_items": human_items,
        "markdown": report_md,
        "human_review_markdown": human_md,
        **paths,
    }
