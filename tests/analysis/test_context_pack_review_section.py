import os
import shutil
import unittest

from reposense.context_pack import build_context_pack
from tests.analysis._context_pack_review_fixture import build_review_context_run


class ContextPackReviewSectionTest(unittest.TestCase):
    def test_review_section_exists_and_artifacts_copied(self):
        run_dir = build_review_context_run()
        try:
            pack = build_context_pack(run_dir)
            review = os.path.join(pack, "REVIEW")
            self.assertTrue(os.path.isdir(review))
            for name in [
                "README.md",
                "ai_maintenance_constraints.md",
                "repository_review_report.md",
                "human_review_required.md",
                "backend_verifier_report.md",
                "code_health_summary.json",
                "permission_risk_report.md",
                "authz_matrix_report.md",
                "authz_negative_test_plan.md",
            ]:
                self.assertTrue(os.path.isfile(os.path.join(review, name)), name)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

