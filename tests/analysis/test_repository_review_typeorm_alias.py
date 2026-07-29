import shutil
import unittest

from reposense.analysis.reports.backend_verifier_report import (
    generate_backend_verifier_report,
)
from reposense.analysis.review.review_engine import generate_repository_review
from tests.analysis.test_typescript_import_graph_schema import build_alias_run


class RepositoryReviewTypeOrmAliasTest(unittest.TestCase):
    def test_backend_and_review_expose_alias_summary(self):
        run_dir = build_alias_run()
        try:
            backend = generate_backend_verifier_report(str(run_dir))
            review = generate_repository_review(str(run_dir))
            self.assertEqual(
                backend["typeorm_alias_resolution"]["status"], "enabled"
            )
            aliases = review["transaction_review"][
                "typeorm_alias_resolution"
            ]
            self.assertEqual(aliases["status"], "enabled")
            self.assertGreater(aliases["resolved_wrapper_calls"], 0)
        finally:
            shutil.rmtree(run_dir.parent, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
