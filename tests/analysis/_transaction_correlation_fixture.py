import os

from reposense.analysis.ai.pattern_export import export_patterns
from reposense.scan import run_scan
from tests._tmpdir import make_temp_dir


def fixture_repo():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "spring_transaction_correlation_min"))


def build_transaction_run():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_dir = make_temp_dir(prefix="transaction_correlation_")
    run_dir = run_scan(
        fixture_repo(),
        run_dir,
        os.path.join(root, "rulesets", "demo_v1"),
        os.path.join(root, "presets", "demo.json"),
    )
    export_patterns(run_dir)
    return run_dir
