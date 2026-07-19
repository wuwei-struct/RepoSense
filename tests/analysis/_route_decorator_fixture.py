import json
import os

from reposense.analysis.authz.authz_export import export_permission_auditor
from tests._tmpdir import make_temp_dir


def fixture_repo():
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "fixtures",
            "repos",
            "route_decorator_classification_min",
        )
    )


def build_decorator_run():
    run_dir = make_temp_dir(prefix="route_decorator_")
    for name, payload in [
        (
            "report.json",
            {
                "run_summary": {"findings_count": 0, "events_count": 0},
                "findings": [],
            },
        ),
        ("event_graph.json", {"nodes": [], "edges": []}),
        ("coverage.json", {"walk": {"included_files": 5}, "warnings": []}),
    ]:
        with open(os.path.join(run_dir, name), "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
    result = export_permission_auditor(run_dir, repo_path=fixture_repo())
    return run_dir, result
