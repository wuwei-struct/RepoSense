import os
import time
import json
import hashlib
from .scan import run_scan
from .verifier import run_verify
from .sarif import run_export_sarif
from .quality_gate import load_gate_config, collect_metrics, evaluate, write_quality_gate
from .patch_exports import run_patch_exports
from .utils import write_json


def _make_run_dir(out_dir):
    ts = int(time.time())
    rid = hashlib.sha1(f"{ts}|ci".encode("utf-8")).hexdigest()[:8]
    run_dir = os.path.join(out_dir, f"run-{ts}-{rid}")
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


def _profile_defaults(profile_name, base):
    from .profiles import resolve_profile
    edition = os.environ.get("REPOSENSE_EDITION", "oss")
    p = resolve_profile(profile_name or "demo", edition=edition)
    return p["ruleset_dir"], p["budget_path"], p["gate_path"]


def run_ci(repo_root, out_dir, profile="demo", ruleset=None, budget=None, gate=None, with_context_pack=False, json_stdout=False, baseline_in=None, baseline_out=None, redact=None):
    base = os.path.dirname(os.path.dirname(__file__))
    out_dir = out_dir or os.path.join(repo_root, ".reposense_ci")
    os.makedirs(out_dir, exist_ok=True)
    run_dir = _make_run_dir(out_dir)
    r_def, b_def, g_def = _profile_defaults(profile, base)
    ruleset = ruleset or r_def
    budget = budget or b_def
    gate = gate or g_def
    times = {}
    outputs = {}
    status_code = 0
    try:
        t0 = time.time()
        try:
            os.makedirs(os.path.join(run_dir, "meta"), exist_ok=True)
            cfgp = os.path.join(run_dir, "meta", "config.json")
            base_cfg = {}
            if os.path.isfile(cfgp):
                try:
                    base_cfg = json.load(open(cfgp, "r", encoding="utf-8"))
                except Exception:
                    base_cfg = {}
            base_cfg["profile"] = profile
            base_cfg["gate_path"] = gate
            base_cfg["edition"] = os.environ.get("REPOSENSE_EDITION", "oss")
            json.dump(base_cfg, open(cfgp, "w", encoding="utf-8"))
        except Exception:
            pass
        rd = run_scan(repo_root, run_dir, ruleset, budget, base_run_dir=None, specs_dir=None)
        try:
            cfgp = os.path.join(rd, "meta", "config.json")
            cfg = json.load(open(cfgp, "r", encoding="utf-8"))
            cfg["profile"] = profile
            cfg["gate_path"] = gate
            cfg["edition"] = os.environ.get("REPOSENSE_EDITION", "oss")
            json.dump(cfg, open(cfgp, "w", encoding="utf-8"))
            # report generation now uses meta/config profile to decide demo marker; no client-side toggling
        except Exception:
            pass
        times["scan_ms"] = int((time.time() - t0) * 1000)
        outputs["run_dir"] = rd
        # verify
        t1 = time.time()
        run_verify(rd, True)
        times["verify_ms"] = int((time.time() - t1) * 1000)
        # export sarif
        t2 = time.time()
        sarif_out = os.path.join(rd, "exports", "report.sarif.json")
        os.makedirs(os.path.join(rd, "exports"), exist_ok=True)
        run_export_sarif(rd, sarif_out)
        times["export_ms"] = int((time.time() - t2) * 1000)
        outputs["sarif_path"] = sarif_out
        # optional context pack
        if with_context_pack:
            outputs["context_pack_zip"] = os.path.join(rd, "exports", "context_pack.zip")
        # gate
        t3 = time.time()
        cfg = load_gate_config(gate)
        from .baseline import compute_diff as _compute_diff, save_baseline as _save_baseline
        bdiff = None
        if baseline_in:
            try:
                tmp_out = os.path.join(rd, "baseline_diff.json")
                # copy baseline_in into run_dir
                try:
                    with open(baseline_in, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    with open(os.path.join(rd, "baseline_in.json"), "w", encoding="utf-8") as f2:
                        json.dump(data, f2, ensure_ascii=False)
                except Exception:
                    pass
                bdiff = _compute_diff(baseline_in, rd, tmp_out, out_md_path=os.path.join(rd, "baseline_diff.md"), current_ruleset_dir=ruleset)
                outputs["baseline_in"] = os.path.join(rd, "baseline_in.json")
                outputs["baseline_diff_json"] = tmp_out
                outputs["baseline_diff_md"] = os.path.join(rd, "baseline_diff.md")
            except Exception:
                bdiff = None
        paths = None
        if bdiff:
            paths = {"baseline_in": os.path.join(rd, "baseline_in.json"), "diff_json": os.path.join(rd, "baseline_diff.json"), "diff_md": os.path.join(rd, "baseline_diff.md")}
        obj = evaluate(collect_metrics(rd), cfg, baseline_diff=bdiff, baseline_paths=paths)
        write_quality_gate(rd, obj)
        times["gate_ms"] = int((time.time() - t3) * 1000)
        outputs["quality_gate_path"] = os.path.join(rd, "quality_gate.json")
        # post patch
        t4 = time.time()
        rc = run_patch_exports(rd)
        try:
            from .redact import scrub_outputs
            ed = os.environ.get("REPOSENSE_EDITION", "oss")
            env_val = os.environ.get("REPOSENSE_REDACT")
            default_on = True if ed == "oss" else True
            enabled = default_on if redact is None else bool(redact)
            if env_val in ("0","1"):
                enabled = (env_val == "1")
            scrub_outputs(rd, repo_root, enabled=enabled)
        except Exception:
            pass
        if baseline_out:
            try:
                _save_baseline(rd, baseline_out, profile=profile, ruleset=ruleset, gate_id=os.path.basename(gate).replace(".json",""))
                outputs["baseline_out"] = baseline_out
            except Exception:
                pass
        times["patch_ms"] = int((time.time() - t4) * 1000)
        # summary
        summary = {
            "profile": profile,
            "ruleset": ruleset,
            "budget": budget,
            "gate": gate,
            "run_dir": rd,
            "outputs": outputs,
            "durations_ms": times,
            "gate_status": obj.get("status"),
        }
        from .versioning import generated_by, ruleset_fingerprint
        try:
            summary["schema_version"] = 1
            summary["generated_by"] = generated_by("0.1.0", os.path.basename(ruleset), ruleset_fingerprint(ruleset), 1)
        except Exception:
            summary["schema_version"] = 1
        summary["redaction_enabled"] = enabled if 'enabled' in locals() else None
        write_json(os.path.join(rd, "ci_summary.json"), summary)
        try:
            from .run_manifest import build_run_manifest
            build_run_manifest(rd, write=True)
        except Exception:
            pass
        if json_stdout:
            print(json.dumps(summary))
        status_code = 0 if obj.get("status") in ("pass", "warn") else 2
    except Exception as e:
        status_code = 1
        if json_stdout:
            print(json.dumps({"error": str(e)}))
        else:
            print(str(e))
    return status_code
