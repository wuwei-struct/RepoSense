import json
import os

from .authz_export import export_permission_auditor
from .authz_matrix_diff import diff_authz_matrix, inferred_only_diff
from .authz_matrix_infer import infer_authz_matrix, render_inferred_yaml
from .authz_matrix_loader import find_contract, load_authz_contract
from .authz_matrix_render import render_matrix_negative_test_plan, render_matrix_report


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def _write_text(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _repo_from_run(run_dir):
    obj = _read_json(os.path.join(run_dir, "permission_surface.json"), {})
    repo = obj.get("repo_path") if isinstance(obj, dict) else None
    return repo if repo and os.path.isdir(str(repo)) else None


def export_authz_matrix(run_dir, repo_path=None, contract_path=None):
    repo = repo_path or _repo_from_run(run_dir)
    if not repo:
        raise ValueError("repo_path is required when run artifacts do not record a readable repository path")
    if not os.path.isdir(repo):
        raise ValueError("repo_path must be an existing directory")
    surface_path = os.path.join(run_dir, "permission_surface.json")
    risks_path = os.path.join(run_dir, "permission_risks.json")
    if not os.path.isfile(surface_path) or not os.path.isfile(risks_path):
        export_permission_auditor(run_dir, repo_path=repo)
    surface = _read_json(surface_path, {})
    risks = _read_json(risks_path, {})
    inferred = infer_authz_matrix(surface, risks)
    event_graph = _read_json(os.path.join(run_dir, "event_graph.json"), {"nodes": []})
    contract = None
    found_contract = find_contract(repo, contract_path)
    if found_contract:
        contract = load_authz_contract(found_contract)
        diff = diff_authz_matrix(contract, surface, event_graph)
    else:
        diff = inferred_only_diff(surface)
    report_md = render_matrix_report(contract, inferred, diff)
    test_plan_md = render_matrix_negative_test_plan(risks, diff)
    paths = {
        "inferred_path": os.path.join(run_dir, "authz_matrix_inferred.yaml"),
        "diff_path": os.path.join(run_dir, "authz_matrix_diff.json"),
        "report_path": os.path.join(run_dir, "authz_matrix_report.md"),
        "negative_test_plan_path": os.path.join(run_dir, "authz_negative_test_plan.md"),
    }
    _write_text(paths["inferred_path"], render_inferred_yaml(inferred))
    _write_json(paths["diff_path"], diff)
    _write_text(paths["report_path"], report_md)
    _write_text(paths["negative_test_plan_path"], test_plan_md)
    if contract:
        paths["loaded_path"] = os.path.join(run_dir, "authz_matrix_loaded.json")
        _write_json(paths["loaded_path"], contract)
    try:
        from ...run_manifest import build_run_manifest

        build_run_manifest(run_dir, write=True)
    except Exception:
        pass
    return {
        "loaded": contract,
        "inferred": inferred,
        "diff": diff,
        "report_markdown": report_md,
        "negative_test_plan_markdown": test_plan_md,
        **paths,
    }

