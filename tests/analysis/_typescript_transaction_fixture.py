import os
import json

from reposense.analysis.ai.pattern_export import export_patterns
from reposense.scan import run_scan
from tests._tmpdir import make_temp_dir


def fixture_repo():
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "fixtures",
            "repos",
            "typescript_transaction_correlation_min",
        )
    )


def build_typescript_transaction_run():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_dir = make_temp_dir(prefix="typescript_transaction_")
    run_dir = run_scan(
        fixture_repo(),
        run_dir,
        os.path.join(root, "rulesets", "demo_v1"),
        os.path.join(root, "presets", "demo.json"),
    )
    export_patterns(run_dir)
    return run_dir


def load_typescript_correlations(run_dir):
    with open(
        os.path.join(run_dir, "transaction_correlations.json"),
        "r",
        encoding="utf-8",
    ) as handle:
        artifact = json.load(handle)
    return [
        item
        for item in artifact.get("correlations") or []
        if item.get("language") == "typescript"
    ]
