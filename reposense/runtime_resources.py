from importlib import metadata, resources
from pathlib import Path, PurePosixPath


class RuntimeResourceError(RuntimeError):
    pass


_SOURCE_ROOT = Path(__file__).resolve().parent.parent

_RESOURCE_MANIFEST = (
    {
        "resource_id": "studio_webui",
        "source_root": "webui",
        "distribution_root": "share/reposense/webui",
        "required_files": (
            "studio/index.html",
            "studio/artifact-cards.js",
            "studio/artifact-cards.css",
            "studio/app-shell.js",
            "studio/app-shell.css",
            "studio/analyze-form.js",
            "studio/run-workbench.js",
            "static/reposense.css",
        ),
    },
    {
        "resource_id": "rulesets",
        "source_root": "rulesets",
        "distribution_root": "share/reposense/rulesets",
        "required_files": (
            "basic/rules.yaml",
            "basic/ruleset_version.json",
            "demo_v1/rules.yaml",
            "demo_v1/ruleset_version.json",
            "specs_v2/rules.yaml",
            "specs_v2/ruleset_version.json",
        ),
    },
    {
        "resource_id": "presets",
        "source_root": "presets",
        "distribution_root": "share/reposense/presets",
        "required_files": (
            "default.json",
            "demo.json",
            "prod_lite.json",
            "prod_deep.json",
            "gates/demo.json",
            "gates/prod_lite.json",
            "gates/prod_deep.json",
        ),
    },
    {
        "resource_id": "specs",
        "source_root": "specs",
        "distribution_root": "share/reposense/specs",
        "required_files": (
            "concepts/async.queue.yaml",
            "concepts/async.scheduler.yaml",
            "concepts/async.workflow.yaml",
            "concepts/concurrency.idempotency.yaml",
            "concepts/concurrency.lock.yaml",
            "concepts/consistency.state_machine.yaml",
            "concepts/consistency.transaction.yaml",
            "concepts/integration.webhook.yaml",
            "concepts/observability.metrics_or_tracing.yaml",
            "concepts/reliability.retry.yaml",
            "concepts/reliability.timeout.yaml",
            "concepts/storage.cache.yaml",
            "concepts/storage.filesystem.yaml",
            "concepts/storage.index.yaml",
            "concepts/storage.kv.yaml",
            "concepts/storage.migration.yaml",
            "rulesets/api_openapi.yaml",
            "rulesets/compose_kv.yaml",
            "rulesets/concurrency_idempotency_text.yaml",
            "rulesets/gha_async.yaml",
            "rulesets/py_cache.yaml",
            "rulesets/py_celery.yaml",
            "rulesets/py_django_atomic.yaml",
            "rulesets/py_fastapi_route.yaml",
            "rulesets/py_flask_route.yaml",
            "rulesets/sql_storage.yaml",
            "rulesets/sql_tx_boundary.yaml",
            "schemas/case.schema.json",
            "schemas/concept.schema.json",
            "schemas/ruleset.schema.json",
            "taxonomies/categories.yaml",
            "taxonomies/evidence_kinds.yaml",
            "taxonomies/risk_types.yaml",
        ),
    },
    {
        "resource_id": "learn_concepts",
        "source_root": "reposense/shared/concepts",
        "distribution_root": "reposense/shared/concepts",
        "required_files": ("concepts.json",),
    },
    {
        "resource_id": "sqlite_schema",
        "source_root": "sql",
        "distribution_root": "share/reposense/sql",
        "required_files": ("schema_v1.sql",),
    },
)


def runtime_resource_manifest():
    return tuple(
        {
            "resource_id": item["resource_id"],
            "source_root": item["source_root"],
            "distribution_root": item["distribution_root"],
            "required_files": tuple(item["required_files"]),
        }
        for item in _RESOURCE_MANIFEST
    )


def _manifest_item(resource_id):
    for item in _RESOURCE_MANIFEST:
        if item["resource_id"] == resource_id:
            return item
    raise RuntimeResourceError(f"unknown runtime resource '{resource_id}'")


def _contains_required(root, item):
    return root.is_dir() and all((root / rel).is_file() for rel in item["required_files"])


def _distribution_root(item):
    try:
        dist = metadata.distribution("reposense")
        dist_files = tuple(dist.files or ())
    except metadata.PackageNotFoundError:
        return None

    marker = PurePosixPath(item["required_files"][0])
    expected = PurePosixPath(item["distribution_root"]) / marker
    expected_parts = expected.parts
    for entry in dist_files:
        normalized = PurePosixPath(str(entry).replace("\\", "/"))
        if normalized.parts[-len(expected_parts) :] != expected_parts:
            continue
        candidates = (Path(dist.locate_file(entry)).resolve(),)
        if item["resource_id"] != "learn_concepts":
            anchor = Path(dist.locate_file("")).resolve()
            candidates += (anchor / item["distribution_root"] / Path(*marker.parts),)
        for marker_path in candidates:
            root = marker_path
            for _ in marker.parts:
                root = root.parent
            if _contains_required(root, item):
                return root
    return None


def _package_concepts_root(item):
    if item["resource_id"] != "learn_concepts":
        return None
    try:
        if hasattr(resources, "files"):
            root = Path(resources.files("reposense.shared.concepts"))
        else:
            with resources.path("reposense.shared.concepts", "concepts.json") as concept_file:
                root = Path(concept_file).parent
    except (FileNotFoundError, ModuleNotFoundError, TypeError):
        return None
    return root if _contains_required(root, item) else None


def _is_source_checkout():
    return (
        (_SOURCE_ROOT / "pyproject.toml").is_file()
        and (_SOURCE_ROOT / "reposense" / "runtime_resources.py").is_file()
    )


def resolve_runtime_resource(resource_id):
    item = _manifest_item(resource_id)
    installed = _package_concepts_root(item) or _distribution_root(item)
    if installed is not None:
        return installed

    if _is_source_checkout():
        source = (_SOURCE_ROOT / item["source_root"]).resolve()
        if _contains_required(source, item):
            return source

    missing = item["required_files"][0]
    raise RuntimeResourceError(
        f"runtime resource '{resource_id}' is missing required file '{missing}'"
    )


def get_studio_webui_dir():
    return resolve_runtime_resource("studio_webui") / "studio"


def get_report_webui_dir():
    return resolve_runtime_resource("studio_webui") / "static"


def get_learn_webui_dir():
    return resolve_runtime_resource("studio_webui") / "static"


def get_rulesets_dir():
    return resolve_runtime_resource("rulesets")


def get_presets_dir():
    return resolve_runtime_resource("presets")


def get_specs_dir():
    return resolve_runtime_resource("specs")


def get_concepts_file():
    return resolve_runtime_resource("learn_concepts") / "concepts.json"


def get_sqlite_schema_file():
    return resolve_runtime_resource("sqlite_schema") / "schema_v1.sql"


def validate_required_runtime_resources():
    resources_found = []
    errors = []
    for item in _RESOURCE_MANIFEST:
        resource_id = item["resource_id"]
        try:
            root = resolve_runtime_resource(resource_id)
            mode = "installed"
            if _is_source_checkout():
                try:
                    root.relative_to(_SOURCE_ROOT)
                    mode = "source"
                except ValueError:
                    pass
            resources_found.append(
                {
                    "resource_id": resource_id,
                    "required_file_count": len(item["required_files"]),
                    "available": True,
                    "mode": mode,
                }
            )
        except RuntimeResourceError as exc:
            resources_found.append(
                {
                    "resource_id": resource_id,
                    "required_file_count": len(item["required_files"]),
                    "available": False,
                    "mode": "unavailable",
                }
            )
            errors.append(str(exc))
    return {
        "ok": not errors,
        "resources": resources_found,
        "errors": errors,
    }
