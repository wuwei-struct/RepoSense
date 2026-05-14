import os
import hashlib
from .utils import write_json
def make_run_dir(base_out, repo_path):
    h = hashlib.sha256(os.path.abspath(repo_path).encode("utf-8")).hexdigest()[:16]
    base_name = os.path.basename(os.path.abspath(base_out))
    if base_name.startswith("run-"):
        run_dir = base_out
    else:
        run_dir = os.path.join(base_out, f"repo-{h}")
    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(os.path.join(run_dir, "parse_cache"), exist_ok=True)
    os.makedirs(os.path.join(run_dir, "evidence"), exist_ok=True)
    os.makedirs(os.path.join(run_dir, "meta"), exist_ok=True)
    return run_dir
def write_manifest(run_dir, manifest):
    write_json(os.path.join(run_dir, "manifest.json"), manifest)
def write_meta(run_dir, tool_version, ruleset_version, config):
    write_json(os.path.join(run_dir, "meta", "tool_version.json"), tool_version)
    write_json(os.path.join(run_dir, "meta", "ruleset_version.json"), ruleset_version)
    cfgp = os.path.join(run_dir, "meta", "config.json")
    base = {}
    try:
        import json
        with open(cfgp, "r", encoding="utf-8") as f:
            base = json.load(f)
    except Exception:
        base = {}
    merged = {**base, **config}
    write_json(cfgp, merged)
def write_event_graph(run_dir, events):
    write_json(os.path.join(run_dir, "event_graph.json"), {"events": events})
def write_report_json(run_dir, report):
    write_json(os.path.join(run_dir, "report.json"), report)
def write_evidence_json(run_dir, eid, data):
    write_json(os.path.join(run_dir, "evidence", f"E{eid}.json"), data)
def write_coverage(run_dir, coverage):
    write_json(os.path.join(run_dir, "coverage.json"), coverage)

