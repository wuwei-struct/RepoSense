import json
import os

from tests._tmpdir import make_temp_dir


def fixture_repo():
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "fixtures",
            "repos",
            "review_context_calibration_min",
        )
    )


def build_context_run():
    run_dir = make_temp_dir(prefix="review_context_run_")
    graph = {
        "nodes": [
            {
                "event_id": "ctx-e1",
                "type": "db_op",
                "meta": {
                    "path": "src/generated/client.ts",
                    "start_line": 2,
                    "db.kind": "db.write",
                },
            },
            {
                "event_id": "ctx-e2",
                "type": "db_op",
                "meta": {
                    "path": "src/database/seeds/demo.seed.ts",
                    "start_line": 2,
                    "db.kind": "db.write",
                },
            },
            {
                "event_id": "ctx-e3",
                "type": "db_op",
                "meta": {
                    "path": "src/templates/service.template.ts",
                    "start_line": 2,
                    "db.kind": "db.write",
                },
            },
            {
                "event_id": "ctx-e4",
                "type": "db_op",
                "meta": {
                    "path": "src/services/order.service.ts",
                    "start_line": 2,
                    "db.kind": "db.write",
                },
            },
            {
                "event_id": "ctx-e5",
                "type": "api",
                "confidence": 0.9,
                "meta": {
                    "path": "src/orders/orders.controller.ts",
                    "start_line": 4,
                    "method": "POST",
                    "route": "/orders",
                },
            },
        ],
        "edges": [],
    }
    artifacts = {
        "event_graph.json": graph,
        "report.json": {
            "run_summary": {"findings_count": 0, "events_count": 5},
            "findings": [],
        },
        "coverage.json": {"walk": {"included_files": 6}, "warnings": []},
        "quality_gate.json": {"status": "pass", "violations": []},
        "api_surface.json": {"endpoints": [], "stats": {}},
    }
    for name, payload in artifacts.items():
        with open(os.path.join(run_dir, name), "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
    return run_dir
