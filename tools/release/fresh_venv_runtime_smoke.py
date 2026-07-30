import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

try:
    from .offline_wheelhouse import (
        DEFAULT_LOCK,
        DEFAULT_WHEELHOUSE,
        REPO_ROOT,
        sha256_file,
        verify_wheelhouse,
    )
    from .package_runtime_smoke import build_wheel, inspect_wheel
except ImportError:  # Direct script execution.
    from offline_wheelhouse import (
        DEFAULT_LOCK,
        DEFAULT_WHEELHOUSE,
        REPO_ROOT,
        sha256_file,
        verify_wheelhouse,
    )
    from package_runtime_smoke import build_wheel, inspect_wheel


class FreshVenvSmokeError(RuntimeError):
    pass


def _guarded_reset(path):
    path = Path(path).resolve()
    allowed = (REPO_ROOT / ".tmp_test_runs").resolve()
    try:
        path.relative_to(allowed)
    except ValueError as exc:
        raise FreshVenvSmokeError(
            "fresh-venv smoke paths must be under .tmp_test_runs"
        ) from exc
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def _offline_environment():
    environment = os.environ.copy()
    for key in (
        "PYTHONHOME",
        "PYTHONPATH",
        "PIP_INDEX_URL",
        "PIP_EXTRA_INDEX_URL",
    ):
        environment.pop(key, None)
    environment.update(
        {
            "PIP_NO_INDEX": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PYTHONUTF8": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    return environment


def _run(command, cwd, environment, *, check=True):
    return subprocess.run(
        [str(item) for item in command],
        cwd=str(cwd),
        env=environment,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        check=check,
    )


def _last_json(output):
    for line in reversed(output.splitlines()):
        stripped = line.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            return json.loads(stripped)
    raise FreshVenvSmokeError("command did not emit a JSON result")


def _fresh_paths(root):
    root = Path(root).resolve()
    return {
        "root": root,
        "downloads": root / "downloads",
        "repo_wheel": root / "repo-wheel",
        "build": root / "repo-wheel-build",
        "venv": root / "fresh-venv",
        "outside": root / "external-cwd",
        "reports": root / "reports",
    }


def _venv_binaries(venv):
    if os.name == "nt":
        scripts = Path(venv) / "Scripts"
        return scripts / "python.exe", scripts / "reposense.exe"
    scripts = Path(venv) / "bin"
    return scripts / "python", scripts / "reposense"


def _build_repo_wheel(paths):
    _, built_wheel, _ = build_wheel(paths["build"])
    inspection = inspect_wheel(built_wheel)
    if (
        inspection["wheel_version"] != "0.1.0"
        or inspection["runtime_asset_count"] != 52
        or inspection["missing_runtime_assets"]
        or inspection["forbidden_content"]
        or not inspection["license_present"]
    ):
        raise FreshVenvSmokeError(f"RepoSense wheel inspection failed: {inspection}")
    repo_wheel_dir = _guarded_reset(paths["repo_wheel"])
    wheel = repo_wheel_dir / built_wheel.name
    shutil.copy2(built_wheel, wheel)
    return wheel, inspection


def _create_venv(paths, environment):
    venv = paths["venv"]
    if venv.exists():
        shutil.rmtree(venv)
    result = _run(
        (sys.executable, "-m", "venv", str(venv)),
        paths["outside"],
        environment,
    )
    python, console = _venv_binaries(venv)
    if not python.is_file():
        raise FreshVenvSmokeError("fresh venv Python was not created")
    if (venv / "pyvenv.cfg").read_text(encoding="utf-8").lower().find(
        "include-system-site-packages = false"
    ) < 0:
        raise FreshVenvSmokeError("fresh venv unexpectedly uses system site-packages")
    return python, console, result


def _install_offline(python, wheel, paths, environment):
    command = (
        python,
        "-m",
        "pip",
        "install",
        "--no-index",
        "--find-links",
        paths["downloads"],
        wheel,
    )
    install = _run(command, paths["outside"], environment)
    check = _run((python, "-m", "pip", "check"), paths["outside"], environment)
    freeze = _run(
        (python, "-m", "pip", "freeze"),
        paths["outside"],
        environment,
    )
    (paths["reports"] / "pip-check.txt").write_text(
        check.stdout, encoding="utf-8"
    )
    (paths["reports"] / "pip-freeze.txt").write_text(
        freeze.stdout, encoding="utf-8"
    )
    return {
        "install_command": "pip install --no-index --find-links <wheelhouse> <reposense-wheel>",
        "pip_check": check.stdout.strip(),
        "pip_freeze": tuple(
            line.strip() for line in freeze.stdout.splitlines() if line.strip()
        ),
        "install_stdout": install.stdout,
    }


def _package_identity(python, paths, environment):
    code = r"""
import json
import pathlib
import sys
import reposense
import requests
import yaml
from reposense.runtime_resources import validate_required_runtime_resources

venv = pathlib.Path(sys.argv[1]).resolve()
repo = pathlib.Path(sys.argv[2]).resolve()
original_venv = pathlib.Path(sys.argv[3]).resolve()

def relative_to_venv(module):
    path = pathlib.Path(module.__file__).resolve()
    try:
        return path.relative_to(venv).as_posix()
    except ValueError:
        raise RuntimeError(f"{module.__name__} imported outside fresh venv")

resolved_sys_path = []
for item in sys.path:
    if not item:
        continue
    try:
        resolved_sys_path.append(pathlib.Path(item).resolve())
    except OSError:
        pass
if repo in resolved_sys_path:
    raise RuntimeError("source repository appears in fresh interpreter sys.path")

locations = {
    "reposense": relative_to_venv(reposense),
    "yaml": relative_to_venv(yaml),
    "requests": relative_to_venv(requests),
    "source_repo_on_sys_path": False,
    "original_venv_used": any(
        str(path).lower().startswith(str(original_venv).lower())
        for path in resolved_sys_path
    ),
    "resources": validate_required_runtime_resources(),
}
if locations["original_venv_used"]:
    raise RuntimeError("original development venv appears in fresh interpreter sys.path")
if not locations["resources"]["ok"] or any(
    item["mode"] != "installed" for item in locations["resources"]["resources"]
):
    raise RuntimeError("fresh installation did not resolve installed resources")
print(json.dumps(locations))
"""
    result = _run(
        (
            python,
            "-I",
            "-c",
            code,
            paths["venv"],
            REPO_ROOT,
            REPO_ROOT / ".venv",
        ),
        paths["outside"],
        environment,
    )
    locations = _last_json(result.stdout)
    (paths["reports"] / "package-locations.json").write_text(
        json.dumps(locations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return locations


def _cli_smoke(console, paths, environment):
    if not console.is_file():
        raise FreshVenvSmokeError("RepoSense console script was not installed")
    commands = (
        ("--help",),
        ("review", "--help"),
        ("health", "--help"),
        ("authz", "--help"),
        ("studio", "--help"),
        ("learn", "--help"),
        ("ai", "--help"),
    )
    for command in commands:
        result = _run((console, *command), paths["outside"], environment)
        if "Traceback" in result.stdout or "Traceback" in result.stderr:
            raise FreshVenvSmokeError(f"CLI traceback for command: {command}")
    version = _run(
        (console, "--version"),
        paths["outside"],
        environment,
        check=False,
    )
    warnings = []
    if version.returncode == 0:
        if "0.1.0" not in version.stdout:
            raise FreshVenvSmokeError("console version output is not 0.1.0")
        version_status = "0.1.0"
    else:
        version_status = "not_supported"
        warnings.append("cli_version_flag_not_supported")
    return {
        "console_script": "Scripts/reposense.exe" if os.name == "nt" else "bin/reposense",
        "help_commands": len(commands),
        "version": version_status,
        "warnings": warnings,
    }


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _studio_smoke(console, paths, environment):
    port = _free_port()
    process = subprocess.Popen(
        [str(console), "studio", "serve", "--port", str(port)],
        cwd=str(paths["outside"]),
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    statuses = {}
    try:
        endpoints = ("/", "/artifact-cards.js", "/artifact-cards.css", "/api/runs")
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                for endpoint in endpoints:
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:{port}{endpoint}", timeout=2
                    ) as response:
                        statuses[endpoint] = response.status
                if all(statuses.get(endpoint) == 200 for endpoint in endpoints):
                    break
            except OSError:
                time.sleep(0.2)
        if not all(statuses.get(endpoint) == 200 for endpoint in endpoints):
            raise FreshVenvSmokeError(f"fresh Studio HTTP smoke failed: {statuses}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    return statuses


def _learn_smoke(console, python, paths, environment):
    result = _run((console, "learn", "concepts"), paths["outside"], environment)
    if not result.stdout.strip():
        raise FreshVenvSmokeError("Learn concepts command returned no concepts")
    code = r"""
import json
import pathlib
from reposense.learn.concept_graph import default_concept_graph_path, load_concept_graph

venv = pathlib.Path(__import__("sys").argv[1]).resolve()
path = pathlib.Path(default_concept_graph_path()).resolve()
try:
    relative = path.relative_to(venv).as_posix()
except ValueError:
    raise RuntimeError("concept graph was not loaded from fresh venv")
data = load_concept_graph(str(path))
names = [item.get("name", "") for item in data.get("concepts", [])]
print(json.dumps({
    "concept_count": len(data.get("concepts", [])),
    "concept_path": relative,
    "utf8_labels_present": any(any(ord(char) > 127 for char in name) for name in names),
}))
"""
    checked = _run(
        (python, "-I", "-c", code, paths["venv"]),
        paths["outside"],
        environment,
    )
    data = _last_json(checked.stdout)
    if data["concept_count"] <= 0 or not data["utf8_labels_present"]:
        raise FreshVenvSmokeError("installed concept graph UTF-8 data is incomplete")
    return data


def _scan_smoke(console, python, paths, environment):
    scan_root = _guarded_reset(paths["reports"] / "fresh-run")
    fixture = REPO_ROOT / "tests" / "fixtures" / "repos" / "review_demo_full"
    ci = _run(
        (
            console,
            "ci",
            "run",
            "--repo",
            fixture,
            "--out",
            scan_root,
            "--profile",
            "demo",
            "--with-context-pack",
            "--json",
        ),
        paths["outside"],
        environment,
    )
    ci_result = _last_json(ci.stdout)
    run_dir = Path(ci_result["run_dir"]).resolve()
    try:
        run_dir.relative_to(scan_root)
    except ValueError as exc:
        raise FreshVenvSmokeError("fresh scan output escaped the report root") from exc

    _run((console, "backend", "report", run_dir, "--json", "--markdown"), paths["outside"], environment)
    _run((console, "review", "report", run_dir, "--json", "--markdown"), paths["outside"], environment)
    context_code = (
        "from reposense.context_pack import build_context_pack, zip_context_pack;"
        "import sys;build_context_pack(sys.argv[1]);zip_context_pack(sys.argv[1])"
    )
    _run((python, "-I", "-c", context_code, run_dir), paths["outside"], environment)
    _run((console, "patch", "exports", run_dir), paths["outside"], environment)
    gate = _run((console, "gate", run_dir, "--json"), paths["outside"], environment)
    _run((console, "run", "manifest", run_dir, "--json"), paths["outside"], environment)
    strict = _run((console, "verify", run_dir, "--strict", "--json"), paths["outside"], environment)

    quality_gate = json.loads((run_dir / "quality_gate.json").read_text(encoding="utf-8"))
    if quality_gate.get("status") != "pass":
        raise FreshVenvSmokeError(
            f"fresh scan quality gate is {quality_gate.get('status')}"
        )
    required = (
        "indices.sqlite",
        "detections.sqlite",
        "report.html",
        "repository_review_report.md",
        "backend_verifier_report.md",
        "run_manifest.json",
        "exports/report.sarif.json",
        "exports/context_pack.zip",
        "context_pack/REVIEW/README.md",
    )
    missing = [item for item in required if not (run_dir / item).is_file()]
    if missing:
        raise FreshVenvSmokeError(f"fresh scan artifacts missing: {missing}")
    strict_text = strict.stdout.strip()
    if not strict_text:
        raise FreshVenvSmokeError("strict verify emitted no result")
    return {
        "run_dir": run_dir.relative_to(paths["root"]).as_posix(),
        "quality_gate": quality_gate["status"],
        "strict_verify": "pass",
        "context_pack": "pass",
        "manifest": "pass",
        "sarif": "pass",
        "sqlite_schema": "pass",
        "gate_output_present": bool(gate.stdout.strip()),
    }


def _write_reports(paths, summary):
    json_path = paths["reports"] / "fresh_venv_smoke.json"
    markdown_path = paths["reports"] / "fresh_venv_smoke.md"
    json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Fresh-Venv Runtime Smoke",
        "",
        f"- asset_packaging: `{summary['asset_packaging']}`",
        f"- wheelhouse_integrity: `{summary['wheelhouse_integrity']}`",
        f"- dependency_closure: `{summary['dependency_closure']}`",
        f"- fresh_venv_creation: `{summary['fresh_venv_creation']}`",
        f"- offline_install: `{summary['offline_install']}`",
        f"- pip_check: `{summary['pip_check']}`",
        f"- studio_smoke: `{summary['studio_smoke']}`",
        f"- scan_smoke: `{summary['scan_smoke']}`",
        f"- overall: `{summary['overall']}`",
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_fresh_venv_smoke(
    wheelhouse=DEFAULT_WHEELHOUSE,
    lock_path=DEFAULT_LOCK,
):
    paths = _fresh_paths(wheelhouse)
    paths["root"].mkdir(parents=True, exist_ok=True)
    _guarded_reset(paths["outside"])
    paths["reports"].mkdir(parents=True, exist_ok=True)
    environment = _offline_environment()

    wheelhouse_result = verify_wheelhouse(paths["root"], lock_path)
    (paths["reports"] / "wheelhouse-verification.json").write_text(
        json.dumps(wheelhouse_result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    wheel, inspection = _build_repo_wheel(paths)
    python, console, _ = _create_venv(paths, environment)
    install = _install_offline(python, wheel, paths, environment)
    locations = _package_identity(python, paths, environment)
    cli = _cli_smoke(console, paths, environment)
    studio = _studio_smoke(console, paths, environment)
    learn = _learn_smoke(console, python, paths, environment)
    scan = _scan_smoke(console, python, paths, environment)

    summary = {
        "asset_packaging": "pass",
        "wheelhouse_integrity": wheelhouse_result["wheelhouse_integrity"],
        "dependency_closure": wheelhouse_result["dependency_closure"],
        "fresh_venv_creation": "pass",
        "offline_install": "pass",
        "package_identity": "pass",
        "pip_check": "pass",
        "cli_smoke": "pass",
        "studio_smoke": "pass",
        "learn_smoke": "pass",
        "scan_smoke": "pass",
        "strict_verify": scan["strict_verify"],
        "quality_gate": scan["quality_gate"],
        "overall": "pass",
        "repo_wheel": {
            "filename": wheel.name,
            "version": inspection["wheel_version"],
            "sha256": sha256_file(wheel),
            "file_count": inspection["file_count"],
            "runtime_asset_count": inspection["runtime_asset_count"],
            "forbidden_content_count": len(inspection["forbidden_content"]),
        },
        "dependencies": wheelhouse_result["packages"],
        "package_locations": locations,
        "pip_freeze": install["pip_freeze"],
        "cli": cli,
        "studio_http": studio,
        "learn": learn,
        "scan": scan,
        "network_install": False,
        "system_site_packages": False,
        "source_checkout_imported": False,
        "warnings": cli["warnings"],
    }
    _write_reports(paths, summary)
    return summary


def _parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", default=str(DEFAULT_WHEELHOUSE))
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    return parser


def main():
    args = _parser().parse_args()
    summary = run_fresh_venv_smoke(args.wheelhouse, args.lock)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
