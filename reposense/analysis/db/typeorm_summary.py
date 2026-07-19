from collections import Counter


def summarize_typeorm_operations(operations):
    kinds = Counter(item.get("kind") for item in operations)
    receivers = Counter(item.get("receiver_kind") for item in operations)
    transaction_contexts = Counter(item.get("transaction_context") for item in operations)
    operation_names = Counter(item.get("operation") for item in operations)
    write_items = [item for item in operations if item.get("kind") == "db.write"]
    return {
        "version": "typeorm_db_summary_v1",
        "total_operations": len(operations),
        "db_reads": int(kinds.get("db.read", 0)),
        "db_writes": int(kinds.get("db.write", 0)),
        "db_transactions": int(kinds.get("db.transaction", 0)),
        "raw_sql_unknown": int(kinds.get("db.query_unknown", 0)),
        "counts_by_receiver_kind": dict(sorted(receivers.items())),
        "counts_by_operation": dict(sorted(operation_names.items())),
        "counts_by_transaction_context": dict(sorted(transaction_contexts.items())),
        "writes_with_explicit_transaction_context": sum(
            1
            for item in write_items
            if item.get("transaction_context") in {"explicit_callback", "query_runner_explicit"}
        ),
        "writes_with_unresolved_transaction_coverage": sum(
            1
            for item in write_items
            if item.get("transaction_context") not in {"explicit_callback", "query_runner_explicit"}
        ),
        "query_builder_reads": sum(
            1 for item in operations
            if item.get("receiver_kind") == "query_builder" and item.get("kind") == "db.read"
        ),
        "query_builder_writes": sum(
            1 for item in operations
            if item.get("receiver_kind") == "query_builder" and item.get("kind") == "db.write"
        ),
        "duplicate_events_removed": 0,
        "limitations": [
            "Static receiver correlation does not implement a complete TypeScript type system.",
            "Unknown transaction context does not prove that a write executes outside a transaction.",
            "Dynamic SQL is retained as db.query_unknown rather than guessed.",
        ],
    }
