import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
import zipfile
from email.parser import Parser
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.8-3.10
    import tomli as tomllib

from pip._vendor.packaging.requirements import Requirement
from pip._vendor.packaging.tags import sys_tags
from pip._vendor.packaging.utils import canonicalize_name, parse_wheel_filename


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WHEELHOUSE = REPO_ROOT / ".tmp_test_runs" / "release_wheelhouse"
DEFAULT_LOCK = REPO_ROOT / "tools" / "release" / "wheelhouse.lock.json"
OFFICIAL_INDEX = "https://pypi.org/simple"
ALLOWED_PACKAGES = frozenset(
    {
        "pyyaml",
        "requests",
        "certifi",
        "charset-normalizer",
        "idna",
        "urllib3",
    }
)
EXPECTED_DIRECT = frozenset({"pyyaml", "requests"})


class WheelhouseError(RuntimeError):
    pass


def normalize_name(name):
    return re.sub(r"[-_.]+", "-", str(name)).lower()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _guarded_reset(path):
    path = Path(path).resolve()
    allowed = (REPO_ROOT / ".tmp_test_runs").resolve()
    try:
        path.relative_to(allowed)
    except ValueError as exc:
        raise WheelhouseError("wheelhouse path must be under .tmp_test_runs") from exc
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def _read_direct_dependencies():
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    raw = tuple(data["project"].get("dependencies") or ())
    requirements = tuple(Requirement(item) for item in raw)
    names = frozenset(normalize_name(item.name) for item in requirements)
    if names != EXPECTED_DIRECT:
        raise WheelhouseError(
            f"unexpected direct runtime dependencies: {sorted(names)}"
        )
    return raw, requirements


def _active_requirements(metadata):
    active = []
    for value in metadata.get_all("Requires-Dist") or ():
        requirement = Requirement(value)
        if requirement.marker is not None and not requirement.marker.evaluate():
            continue
        active.append(requirement)
    return tuple(active)


def read_wheel_metadata(path):
    path = Path(path)
    if path.suffix.lower() != ".whl":
        raise WheelhouseError(f"non-wheel distribution rejected: {path.name}")
    try:
        parsed_name, parsed_version, _, filename_tags = parse_wheel_filename(path.name)
    except Exception as exc:
        raise WheelhouseError(f"invalid wheel filename: {path.name}") from exc
    with zipfile.ZipFile(path) as archive:
        names = tuple(archive.namelist())
        metadata_files = [name for name in names if name.endswith(".dist-info/METADATA")]
        wheel_files = [name for name in names if name.endswith(".dist-info/WHEEL")]
        if len(metadata_files) != 1 or len(wheel_files) != 1:
            raise WheelhouseError(f"wheel metadata layout invalid: {path.name}")
        metadata = Parser().parsestr(
            archive.read(metadata_files[0]).decode("utf-8", errors="strict")
        )
        wheel_metadata = Parser().parsestr(
            archive.read(wheel_files[0]).decode("utf-8", errors="strict")
        )
    metadata_name = normalize_name(metadata.get("Name", ""))
    metadata_version = metadata.get("Version", "")
    if metadata_name != normalize_name(parsed_name):
        raise WheelhouseError(f"wheel name metadata mismatch: {path.name}")
    if metadata_version != str(parsed_version):
        raise WheelhouseError(f"wheel version metadata mismatch: {path.name}")
    declared_tags = tuple(sorted(wheel_metadata.get_all("Tag") or ()))
    filename_tag_strings = tuple(sorted(str(tag) for tag in filename_tags))
    if not declared_tags or set(declared_tags) != set(filename_tag_strings):
        raise WheelhouseError(f"wheel tag metadata mismatch: {path.name}")
    return {
        "name": metadata.get("Name"),
        "normalized_name": metadata_name,
        "version": metadata_version,
        "tags": filename_tag_strings,
        "requirements": _active_requirements(metadata),
    }


def _environment_contract():
    return {
        "target_python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "implementation": platform.python_implementation(),
        "platform": sys.platform,
        "architecture": platform.machine(),
        "platform_tag": sysconfig.get_platform(),
    }


def _validate_lock_shape(lock):
    if lock.get("schema_version") != 1:
        raise WheelhouseError("unsupported wheelhouse lock schema")
    if lock.get("forbidden_sdist") is not True:
        raise WheelhouseError("wheelhouse lock must forbid sdists")
    if lock.get("expected_source") != OFFICIAL_INDEX:
        raise WheelhouseError("wheelhouse lock source must be official PyPI")
    current = _environment_contract()
    for key, value in current.items():
        if lock.get(key) != value:
            raise WheelhouseError(
                f"wheelhouse target mismatch for {key}: expected {value}"
            )
    packages = tuple(lock.get("packages") or ())
    names = [item.get("normalized_name") for item in packages]
    if len(names) != len(set(names)):
        raise WheelhouseError("wheelhouse lock contains duplicate package names")
    if set(names) != ALLOWED_PACKAGES:
        raise WheelhouseError(
            f"wheelhouse package set mismatch: {sorted(set(names))}"
        )
    for item in packages:
        if item.get("dependency_type") not in {"direct", "transitive"}:
            raise WheelhouseError(
                f"invalid dependency type for {item.get('normalized_name')}"
            )
        expected_type = (
            "direct"
            if item.get("normalized_name") in EXPECTED_DIRECT
            else "transitive"
        )
        if item.get("dependency_type") != expected_type:
            raise WheelhouseError(
                f"dependency type mismatch for {item.get('normalized_name')}"
            )
        if not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", ""))):
            raise WheelhouseError(
                f"invalid SHA-256 for {item.get('normalized_name')}"
            )
        if item.get("expected_source") != OFFICIAL_INDEX:
            raise WheelhouseError(
                f"invalid source for {item.get('normalized_name')}"
            )
        if not item.get("exact_version") or not item.get("filename"):
            raise WheelhouseError(
                f"incomplete lock item for {item.get('normalized_name')}"
            )
        if not item.get("wheel_tags"):
            raise WheelhouseError(
                f"missing wheel tags for {item.get('normalized_name')}"
            )
    return packages


def load_lock(lock_path=DEFAULT_LOCK):
    path = Path(lock_path)
    if not path.is_file():
        raise WheelhouseError(f"wheelhouse lock missing: {path.name}")
    lock = json.loads(path.read_text(encoding="utf-8"))
    _validate_lock_shape(lock)
    return lock


def verify_wheelhouse(wheelhouse=DEFAULT_WHEELHOUSE, lock_path=DEFAULT_LOCK):
    wheelhouse = Path(wheelhouse).resolve()
    downloads = wheelhouse / "downloads"
    lock = load_lock(lock_path)
    packages = {item["normalized_name"]: item for item in lock["packages"]}
    if not downloads.is_dir():
        raise WheelhouseError("wheelhouse downloads directory is missing")
    files = tuple(sorted(path for path in downloads.iterdir() if path.is_file()))
    non_wheels = [path.name for path in files if path.suffix.lower() != ".whl"]
    if non_wheels:
        raise WheelhouseError(f"non-wheel files rejected: {non_wheels}")
    expected_filenames = {item["filename"] for item in packages.values()}
    actual_filenames = {path.name for path in files}
    missing = sorted(expected_filenames - actual_filenames)
    extra = sorted(actual_filenames - expected_filenames)
    if missing:
        raise WheelhouseError(f"wheelhouse files missing: {missing}")
    if extra:
        raise WheelhouseError(f"unexpected wheelhouse files: {extra}")

    compatible_tags = set(sys_tags())
    metadata_by_name = {}
    for path in files:
        metadata = read_wheel_metadata(path)
        name = metadata["normalized_name"]
        if name not in packages:
            raise WheelhouseError(f"unexpected package wheel: {name}")
        item = packages[name]
        if path.name != item["filename"]:
            raise WheelhouseError(f"wheel filename mismatch for {name}")
        if metadata["version"] != item["exact_version"]:
            raise WheelhouseError(f"wheel version mismatch for {name}")
        if tuple(metadata["tags"]) != tuple(item["wheel_tags"]):
            raise WheelhouseError(f"wheel tags mismatch for {name}")
        if sha256_file(path) != item["sha256"]:
            raise WheelhouseError(f"wheel hash mismatch for {name}")
        parsed_tags = parse_wheel_filename(path.name)[3]
        if not compatible_tags.intersection(parsed_tags):
            raise WheelhouseError(f"wheel is not compatible with this interpreter: {path.name}")
        metadata_by_name[name] = metadata

    relationships = {}
    for name, metadata in metadata_by_name.items():
        dependencies = []
        for requirement in metadata["requirements"]:
            dependency = normalize_name(requirement.name)
            if dependency not in packages:
                raise WheelhouseError(
                    f"dependency closure contains unexpected package: {dependency}"
                )
            installed_version = packages[dependency]["exact_version"]
            if requirement.specifier and not requirement.specifier.contains(
                installed_version, prereleases=True
            ):
                raise WheelhouseError(
                    f"dependency version does not satisfy {requirement}"
                )
            dependencies.append(
                {
                    "normalized_name": dependency,
                    "specifier": str(requirement.specifier),
                }
            )
        relationships[name] = sorted(
            dependencies, key=lambda item: item["normalized_name"]
        )
        if relationships[name] != packages[name].get("dependencies", []):
            raise WheelhouseError(f"dependency relationship mismatch for {name}")

    return {
        "wheelhouse_integrity": "pass",
        "dependency_closure": "pass",
        "package_count": len(packages),
        "packages": [
            {
                "normalized_name": name,
                "version": packages[name]["exact_version"],
                "filename": packages[name]["filename"],
                "sha256": packages[name]["sha256"],
            }
            for name in sorted(packages)
        ],
        "forbidden_sdist": True,
        "extra_files": [],
        "missing_files": [],
    }


def _build_lock(downloads):
    _, direct_requirements = _read_direct_dependencies()
    direct_names = {normalize_name(item.name) for item in direct_requirements}
    entries = []
    metadata_by_name = {}
    for path in sorted(Path(downloads).glob("*.whl")):
        metadata = read_wheel_metadata(path)
        name = metadata["normalized_name"]
        if name in metadata_by_name:
            raise WheelhouseError(f"multiple wheels selected for package: {name}")
        metadata_by_name[name] = metadata
    if set(metadata_by_name) != ALLOWED_PACKAGES:
        raise WheelhouseError(
            f"downloaded package set mismatch: {sorted(metadata_by_name)}"
        )
    for name in sorted(metadata_by_name):
        metadata = metadata_by_name[name]
        dependencies = []
        for requirement in metadata["requirements"]:
            dependency = normalize_name(requirement.name)
            if dependency not in ALLOWED_PACKAGES:
                raise WheelhouseError(
                    f"unexpected dependency selected by metadata: {dependency}"
                )
            dependencies.append(
                {
                    "normalized_name": dependency,
                    "specifier": str(requirement.specifier),
                }
            )
        path = next(
            item
            for item in Path(downloads).glob("*.whl")
            if normalize_name(read_wheel_metadata(item)["name"]) == name
        )
        entries.append(
            {
                "name": metadata["name"],
                "normalized_name": name,
                "exact_version": metadata["version"],
                "filename": path.name,
                "wheel_tags": list(metadata["tags"]),
                "sha256": sha256_file(path),
                "dependency_type": "direct" if name in direct_names else "transitive",
                "expected_source": OFFICIAL_INDEX,
                "dependencies": sorted(
                    dependencies, key=lambda item: item["normalized_name"]
                ),
            }
        )
    environment = _environment_contract()
    return {
        "schema_version": 1,
        **environment,
        "repo_wheel_version": "0.1.0",
        "forbidden_sdist": True,
        "expected_source": OFFICIAL_INDEX,
        "packages": entries,
    }


def _write_report(report, json_path, markdown_path):
    json_path = Path(json_path)
    markdown_path = Path(markdown_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Offline Wheelhouse Verification",
        "",
        f"- wheelhouse_integrity: `{report['wheelhouse_integrity']}`",
        f"- dependency_closure: `{report['dependency_closure']}`",
        f"- package_count: {report['package_count']}",
        "- source: official PyPI",
        "- sdists: rejected",
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare_wheelhouse(
    wheelhouse=DEFAULT_WHEELHOUSE,
    lock_path=DEFAULT_LOCK,
    *,
    allow_network=False,
    refresh_lock=False,
):
    if not allow_network:
        raise WheelhouseError("network preparation requires --allow-network")
    lock_path = Path(lock_path)
    if lock_path.exists() and not refresh_lock:
        raise WheelhouseError(
            "wheelhouse lock already exists; use --verify or explicit --refresh-lock"
        )
    wheelhouse = Path(wheelhouse).resolve()
    wheelhouse.mkdir(parents=True, exist_ok=True)
    downloads = _guarded_reset(wheelhouse / "downloads")
    direct, _ = _read_direct_dependencies()
    command = (
        sys.executable,
        "-m",
        "pip",
        "--isolated",
        "download",
        "--disable-pip-version-check",
        "--only-binary=:all:",
        "--dest",
        str(downloads),
        "--index-url",
        OFFICIAL_INDEX,
        *direct,
    )
    environment = os.environ.copy()
    environment.pop("PIP_INDEX_URL", None)
    environment.pop("PIP_EXTRA_INDEX_URL", None)
    result = subprocess.run(
        command,
        cwd=str(wheelhouse),
        env=environment,
        text=True,
        capture_output=True,
        check=True,
    )
    files = tuple(sorted(downloads.iterdir()))
    if not files or any(path.suffix.lower() != ".whl" for path in files):
        raise WheelhouseError("official download did not produce wheel-only content")
    lock = _build_lock(downloads)
    temporary_lock = wheelhouse / "wheelhouse.lock.candidate.json"
    temporary_lock.write_text(
        json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = verify_wheelhouse(wheelhouse, temporary_lock)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(temporary_lock, lock_path)
    temporary_lock.unlink()
    return report, result


def _parser():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--refresh-lock", action="store_true")
    parser.add_argument("--wheelhouse", default=str(DEFAULT_WHEELHOUSE))
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--json-report")
    parser.add_argument("--markdown-report")
    return parser


def main():
    args = _parser().parse_args()
    wheelhouse = Path(args.wheelhouse)
    reports = wheelhouse / "reports"
    json_report = Path(args.json_report or reports / "wheelhouse-verification.json")
    markdown_report = Path(
        args.markdown_report or reports / "wheelhouse-verification.md"
    )
    if args.prepare:
        report, _ = prepare_wheelhouse(
            wheelhouse,
            args.lock,
            allow_network=args.allow_network,
            refresh_lock=args.refresh_lock,
        )
    else:
        if args.allow_network or args.refresh_lock:
            raise WheelhouseError(
                "--allow-network/--refresh-lock are valid only with --prepare"
            )
        report = verify_wheelhouse(wheelhouse, args.lock)
    _write_report(report, json_report, markdown_report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
