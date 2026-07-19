from .typescript_transaction_correlation import (
    correlate_typescript_transactions,
)


def export_typescript_transaction_correlations(run_dir, repo_path):
    correlations, summary = correlate_typescript_transactions(
        run_dir, repo_path
    )
    return {"correlations": correlations, "summary": summary}
