import json
import os

from tests._tmpdir import make_temp_dir


def build_learn_ui_fixture():
    root = make_temp_dir(prefix="learn-ui-fixture-")
    cases_dir = os.path.join(root, "cases_lib")
    os.makedirs(os.path.join(cases_dir, "cases"), exist_ok=True)
    concepts_path = os.path.join(root, "concepts.json")

    concepts = {
        "version": "test",
        "concepts": [
            {
                "concept_id": "data.transaction_boundary",
                "name": "Transaction Boundary",
                "summary": "Atomic unit for DB writes.",
                "tags": ["data", "transaction"],
                "learning_objectives": ["Identify @Transactional evidence"],
                "anti_patterns": ["write without boundary"],
                "prerequisites": [],
                "related": ["reliability.idempotency"],
            },
            {
                "concept_id": "reliability.idempotency",
                "name": "Idempotency",
                "summary": "Avoid duplicated side effects.",
                "tags": ["reliability", "dedupe"],
                "learning_objectives": ["Use idempotency key"],
                "anti_patterns": ["no dedupe key"],
                "prerequisites": [],
                "related": ["data.transaction_boundary"],
            },
        ],
    }

    case_a = {
        "case_id": "case-a",
        "concept_id": "data.transaction_boundary",
        "title": "Order service transaction",
        "level": 2,
        "repo_ref": "repo-alpha",
        "rule_id": "tx.required",
        "labels": ["pattern", "positive"],
        "metadata": {"language": "java", "has_closure": True, "distributed_signal": True},
        "explain": {
            "what": "Found transaction boundary around DB writes.",
            "why": "Prevents partial commit.",
            "how": "Use framework transaction annotation.",
            "risk": "Without it, inconsistent state may happen.",
        },
        "closure": {"api": True, "queue": False, "db": True},
        "evidence_refs": [
            {
                "path": "src/main/java/demo/OrderService.java",
                "start_line": 18,
                "end_line": 23,
                "rule_id": "tx.required",
                "snippet": "@Transactional\npublic void placeOrder() {\n  repo.save(entity);\n}",
            }
        ],
    }

    case_b = {
        "case_id": "case-b",
        "concept_id": "reliability.idempotency",
        "title": "Request dedupe key check",
        "level": 1,
        "repo_ref": "repo-alpha",
        "rule_id": "idem.key",
        "labels": ["pattern", "anti-pattern"],
        "metadata": {"language": "python"},
        "explain": {
            "what": "Found request key before write.",
            "why": "Avoid repeated side effects.",
            "how": "Check key existence first.",
            "risk": "Repeated charge/order may happen.",
        },
        "evidence_refs": [
            {
                "path": "app/service.py",
                "start_line": 40,
                "end_line": 46,
                "rule_id": "idem.key",
                "snippet": "if key_exists(req.id):\n    return\nsave_order(req)",
            }
        ],
    }

    with open(concepts_path, "w", encoding="utf-8") as f:
        json.dump(concepts, f, ensure_ascii=False)
    with open(os.path.join(cases_dir, "cases", "case-a.json"), "w", encoding="utf-8") as f:
        json.dump(case_a, f, ensure_ascii=False)
    with open(os.path.join(cases_dir, "cases", "case-b.json"), "w", encoding="utf-8") as f:
        json.dump(case_b, f, ensure_ascii=False)
    with open(os.path.join(cases_dir, "cases_index.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "total_cases": 2,
                "cases": [
                    {
                        "case_id": "case-a",
                        "concept_id": "data.transaction_boundary",
                        "level": 2,
                        "labels": ["pattern", "positive"],
                        "language": "java",
                    },
                    {
                        "case_id": "case-b",
                        "concept_id": "reliability.idempotency",
                        "level": 1,
                        "labels": ["pattern", "anti-pattern"],
                        "language": "python",
                    },
                ],
            },
            f,
            ensure_ascii=False,
        )
    return {"root": root, "cases_dir": cases_dir, "concepts_path": concepts_path}
