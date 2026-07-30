import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import zipfile
from email.parser import Parser
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORK_ROOT = REPO_ROOT / ".tmp_test_runs" / "package_runtime_smoke"
STAGE_ENTRIES = (
    "LICENSE",
    "README.md",
    "pyproject.toml",
    "presets",
    "reposense",
    "rulesets",
    "sql",
    "specs",
    "webui",
)
FORBIDDEN_PARTS = {
    ".reposense_real_repo_smoke",
    ".reposense_review_demo",
    ".tmp_test_runs",
    ".venv",
    "docs",
    "screenshots",
    "tests",
}


def _run(command, cwd, *, capture=True):
    env = os.environ.copy()
    env["PIP_NO_INDEX"] = "1"
    return subprocess.run(
        [str(item) for item in command],
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=capture,
        check=True,
    )


def _reset_dir(path):
    path = Path(path).resolve()
    allowed = (REPO_ROOT / ".tmp_test_runs").resolve()
    try:
        path.relative_to(allowed)
    except ValueError:
        raise RuntimeError("package smoke work directory must be under .tmp_test_runs")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def _copy_source_tree(stage):
    for entry in STAGE_ENTRIES:
        source = REPO_ROOT / entry
        target = stage / entry
        if source.is_dir():
            shutil.copytree(
                source,
                target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
            )
        else:
            shutil.copy2(source, target)


def build_wheel(work_root=DEFAULT_WORK_ROOT):
    work_root = _reset_dir(work_root)
    stage = work_root / "source"
    dist_dir = work_root / "dist"
    stage.mkdir()
    dist_dir.mkdir()
    _copy_source_tree(stage)
    result = _run(
        (
            sys.executable,
            "-m",
            "pip",
            "wheel",
            ".",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            dist_dir,
        ),
        stage,
    )
    wheels = tuple(dist_dir.glob("reposense-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected one RepoSense wheel, found {len(wheels)}")
    return work_root, wheels[0], result


def _load_runtime_manifest_from_source():
    sys.path.insert(0, str(REPO_ROOT))
    try:
        from reposense.runtime_resources import runtime_resource_manifest

        return runtime_resource_manifest()
    finally:
        if sys.path and sys.path[0] == str(REPO_ROOT):
            sys.path.pop(0)


def _archive_name_for(item, relative_path):
    if item["resource_id"] == "learn_concepts":
        return PurePosixPath(item["distribution_root"]) / relative_path
    return PurePosixPath(item["distribution_root"]) / relative_path


def inspect_wheel(wheel_path):
    manifest = _load_runtime_manifest_from_source()
    with zipfile.ZipFile(wheel_path) as archive:
        names = tuple(sorted(archive.namelist()))
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        package_metadata = Parser().parsestr(
            archive.read(metadata_name).decode("utf-8", errors="strict")
        )

    missing = []
    matched_assets = []
    for item in manifest:
        for relative_path in item["required_files"]:
            suffix = _archive_name_for(item, relative_path).as_posix()
            matches = [name for name in names if name.endswith(suffix)]
            if not matches:
                missing.append(f"{item['resource_id']}:{relative_path}")
            else:
                matched_assets.append(matches[0])

    forbidden = []
    for name in names:
        parts = set(PurePosixPath(name).parts)
        lower = name.lower()
        if parts.intersection(FORBIDDEN_PARTS):
            forbidden.append(name)
        elif any(part.startswith((".reposense_", ".tmp_")) for part in parts):
            forbidden.append(name)
        elif lower.endswith((".env", ".log", ".sqlite", ".db")):
            forbidden.append(name)

    licenses = [name for name in names if name.endswith(".dist-info/licenses/LICENSE")]
    return {
        "wheel_file": Path(wheel_path).name,
        "wheel_size_bytes": Path(wheel_path).stat().st_size,
        "wheel_version": package_metadata.get("Version"),
        "file_count": len(names),
        "runtime_asset_count": len(set(matched_assets)),
        "missing_runtime_assets": sorted(missing),
        "forbidden_content": sorted(set(forbidden)),
        "license_present": bool(licenses),
        "archive_names": names,
    }


def install_target(wheel_path, work_root):
    target = Path(work_root) / "target"
    target.mkdir()
    _run(
        (
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            target,
            wheel_path,
        ),
        work_root,
    )
    return target


def _target_command(target, mode, *extra):
    runner = Path(__file__).resolve()
    return (
        sys.executable,
        "-I",
        runner,
        "--target-runner",
        mode,
        "--target",
        target,
        "--forbid-root",
        REPO_ROOT,
        *extra,
    )


def _outside_dir(work_root):
    outside = Path(work_root) / "outside-cwd"
    outside.mkdir(exist_ok=True)
    return outside


def _run_target(target, work_root, mode, *extra):
    result = _run(
        _target_command(target, mode, *extra),
        _outside_dir(work_root),
    )
    return result.stdout.strip()


def _last_json(output):
    lines = [line for line in output.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("target runner produced no JSON output")
    return json.loads(lines[-1])


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _studio_smoke(target, work_root):
    port = _free_port()
    command = _target_command(target, "studio", "--port", str(port))
    process = subprocess.Popen(
        [str(item) for item in command],
        cwd=str(_outside_dir(work_root)),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    statuses = {}
    try:
        deadline = time.time() + 20
        paths = ("/", "/artifact-cards.js", "/artifact-cards.css", "/api/runs")
        while time.time() < deadline:
            try:
                for path in paths:
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:{port}{path}", timeout=2
                    ) as response:
                        statuses[path] = response.status
                if all(statuses.get(path) == 200 for path in paths):
                    break
            except OSError:
                time.sleep(0.2)
        if not all(statuses.get(path) == 200 for path in paths):
            raise RuntimeError(f"installed Studio HTTP smoke failed: {statuses}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    return statuses


def run_target_smoke(wheel_path, work_root):
    target = install_target(wheel_path, work_root)
    resources_result = _last_json(_run_target(target, work_root, "resources"))
    cli_commands = (
        ("--help",),
        ("studio", "--help"),
        ("learn", "--help"),
        ("review", "--help"),
        ("health", "--help"),
        ("authz", "--help"),
    )
    for command in cli_commands:
        _run_target(target, work_root, "cli", "--", *command)
    concepts_result = _last_json(_run_target(target, work_root, "concepts"))
    specs_result = _last_json(_run_target(target, work_root, "specs"))
    ci_out = Path(work_root) / "installed-ci"
    fixture = REPO_ROOT / "tests" / "fixtures" / "repos" / "review_demo_full"
    ci_result = _last_json(
        _run_target(
            target,
            work_root,
            "ci",
            "--fixture",
            str(fixture),
            "--out",
            str(ci_out),
        )
    )
    studio_statuses = _studio_smoke(target, work_root)
    return {
        "target_package_import": resources_result["package_import"],
        "resource_validation": resources_result["validation"],
        "cli_help_commands": len(cli_commands),
        "concept_count": concepts_result["concept_count"],
        "specs_ok": specs_result["ok"],
        "ci_gate_status": ci_result["gate_status"],
        "studio_http": studio_statuses,
    }


def _write_summary(work_root, summary):
    json_path = Path(work_root) / "package_runtime_smoke.json"
    md_path = Path(work_root) / "package_runtime_smoke.md"
    json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Package Runtime Smoke",
        "",
        f"- asset_packaging: `{summary['asset_packaging']}`",
        f"- target_install_smoke: `{summary['target_install_smoke']}`",
        f"- fresh_venv_offline_smoke: `{summary['fresh_venv_offline_smoke']}`",
        f"- wheel: `{summary['wheel']['wheel_file']}`",
        f"- wheel files: {summary['wheel']['file_count']}",
        f"- runtime assets checked: {summary['wheel']['runtime_asset_count']}",
        "",
        "Dependency-neutral target smoke passed; fresh-venv offline dependency smoke pending.",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def run_package_runtime_smoke(work_root=DEFAULT_WORK_ROOT):
    work_root, wheel, _ = build_wheel(work_root)
    wheel_result = inspect_wheel(wheel)
    asset_ok = (
        wheel_result["wheel_version"] == "0.1.0"
        and not wheel_result["missing_runtime_assets"]
        and not wheel_result["forbidden_content"]
        and wheel_result["license_present"]
    )
    if not asset_ok:
        raise RuntimeError(
            "wheel runtime asset inspection failed: "
            + json.dumps(
                {
                    "missing": wheel_result["missing_runtime_assets"],
                    "forbidden": wheel_result["forbidden_content"],
                    "version": wheel_result["wheel_version"],
                    "license": wheel_result["license_present"],
                }
            )
        )
    target_result = run_target_smoke(wheel, work_root)
    summary = {
        "asset_packaging": "pass",
        "target_install_smoke": "pass",
        "fresh_venv_offline_smoke": "pending",
        "wheel": {key: value for key, value in wheel_result.items() if key != "archive_names"},
        "target": target_result,
        "declared_direct_runtime_dependencies": ("PyYAML>=6.0", "requests>=2.31"),
        "offline_wheelhouse_missing": (
            "PyYAML",
            "requests",
            "certifi",
            "charset-normalizer",
            "idna",
            "urllib3",
        ),
        "warnings": (
            "fresh_venv_offline_dependency_smoke_pending",
            "sdist_not_checked_build_module_unavailable",
        ),
    }
    json_path, md_path = _write_summary(work_root, summary)
    summary["summary_json"] = json_path.name
    summary["summary_markdown"] = md_path.name
    return summary


def _prepare_target(target, forbid_root):
    target = Path(target).resolve()
    forbid_root = Path(forbid_root).resolve()
    filtered = []
    for value in sys.path:
        if not value:
            continue
        try:
            resolved = Path(value).resolve()
        except OSError:
            filtered.append(value)
            continue
        if resolved == forbid_root:
            continue
        filtered.append(value)
    sys.path[:] = [str(target)] + filtered
    import reposense

    package_file = Path(reposense.__file__).resolve()
    try:
        package_file.relative_to(target)
    except ValueError:
        raise RuntimeError("target smoke imported RepoSense outside target")
    return target, package_file


def _target_runner(args):
    target, package_file = _prepare_target(args.target, args.forbid_root)
    if args.runner_mode == "resources":
        from reposense.runtime_resources import validate_required_runtime_resources

        validation = validate_required_runtime_resources()
        if not validation["ok"] or any(
            item["mode"] != "installed" for item in validation["resources"]
        ):
            raise RuntimeError(f"installed runtime resources invalid: {validation}")
        print(
            json.dumps(
                {
                    "package_import": package_file.relative_to(target).as_posix(),
                    "validation": validation,
                }
            )
        )
        return 0
    if args.runner_mode == "cli":
        from reposense.cli import main

        command = list(args.command)
        if command and command[0] == "--":
            command.pop(0)
        sys.argv = ["reposense"] + command
        try:
            main()
        except SystemExit as exc:
            return int(exc.code or 0)
        return 0
    if args.runner_mode == "concepts":
        from reposense.learn.concept_graph import default_concept_graph_path, load_concept_graph

        graph = load_concept_graph(default_concept_graph_path())
        print(json.dumps({"concept_count": len(graph.get("concepts") or [])}))
        return 0
    if args.runner_mode == "specs":
        from reposense.runtime_resources import get_specs_dir
        from reposense.specs import check_specs

        result = check_specs(get_specs_dir())
        print(json.dumps({"ok": result["ok"], "errors": result["errors"]}))
        return 0 if result["ok"] else 2
    if args.runner_mode == "ci":
        from reposense.ci import run_ci

        code = run_ci(
            args.fixture,
            args.out,
            profile="demo",
            with_context_pack=False,
            json_stdout=False,
        )
        runs = sorted(Path(args.out).glob("run-*"))
        gate_status = "missing"
        if runs:
            gate = json.loads((runs[-1] / "quality_gate.json").read_text(encoding="utf-8"))
            gate_status = gate.get("status")
        print(json.dumps({"exit_code": code, "gate_status": gate_status}))
        return int(code)
    if args.runner_mode == "studio":
        from reposense.studio.server import run_server

        run_server(args.port)
        return 0
    raise RuntimeError(f"unknown target runner mode: {args.runner_mode}")


def _parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("asset-and-target",), default="asset-and-target")
    parser.add_argument("--work-root", default=str(DEFAULT_WORK_ROOT))
    parser.add_argument("--target-runner", dest="runner_mode", help=argparse.SUPPRESS)
    parser.add_argument("--target", help=argparse.SUPPRESS)
    parser.add_argument("--forbid-root", help=argparse.SUPPRESS)
    parser.add_argument("--fixture", help=argparse.SUPPRESS)
    parser.add_argument("--out", help=argparse.SUPPRESS)
    parser.add_argument("--port", type=int, help=argparse.SUPPRESS)
    parser.add_argument("command", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
    return parser


def main():
    args = _parser().parse_args()
    if args.runner_mode:
        return _target_runner(args)
    summary = run_package_runtime_smoke(args.work_root)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
