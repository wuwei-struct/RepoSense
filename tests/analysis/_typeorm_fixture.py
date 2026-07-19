import json
from pathlib import Path

from reposense.parsers.typescript_typeorm import detect_typeorm_operations


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "repos" / "typeorm_db_operations_min"


def service_operations():
    path = FIXTURE / "src" / "user.service.ts"
    return detect_typeorm_operations(path.read_text(encoding="utf-8").splitlines())


def false_positive_operations():
    path = FIXTURE / "src" / "false-positives.ts"
    return detect_typeorm_operations(path.read_text(encoding="utf-8").splitlines())


def write_minimal_run(run_dir, operations):
    run_dir = Path(run_dir)
    repo = FIXTURE
    (run_dir / "evidence").mkdir(parents=True, exist_ok=True)
    nodes = []
    for index, item in enumerate(operations, start=1):
        evidence_id = f"E{index}"
        file_path = repo / "src" / "user.service.ts"
        evidence = {
            "path": str(file_path),
            "start_line": item["line_start"],
            "end_line": item["line_end"],
            "snippet": file_path.read_text(encoding="utf-8").splitlines()[item["line_start"] - 1],
        }
        (run_dir / "evidence" / f"{evidence_id}.json").write_text(
            json.dumps(evidence),
            encoding="utf-8",
        )
        nodes.append(
            {
                "event_id": f"N{index}",
                "type": "tx_boundary" if item["kind"] == "db.transaction" else "db_op",
                "confidence": item["confidence"],
                "evidence": [evidence_id],
                "meta": {
                    "framework": "typeorm",
                    "language": "typescript",
                    "db.kind": item["kind"],
                    "db.op": item["operation"],
                    "receiver_kind": item["receiver_kind"],
                    "receiver_name": item["receiver_name"],
                    "entity_hint": item["entity"],
                    "transaction_context": item["transaction_context"],
                    "scope": item["scope"],
                    "signals": item["signals"],
                    "limitations": item["limitations"],
                },
            }
        )
    (run_dir / "manifest.json").write_text(
        json.dumps({"repo_root": str(repo)}),
        encoding="utf-8",
    )
    (run_dir / "event_graph.json").write_text(
        json.dumps({"nodes": nodes, "edges": []}),
        encoding="utf-8",
    )
    return run_dir
