import os
import shutil
import unittest

from reposense.context_pack import build_context_pack
from tests.analysis._context_pack_review_fixture import build_review_context_run


class ContextPackAiMaintenanceConstraintsTest(unittest.TestCase):
    def test_constraints_content(self):
        run_dir = build_review_context_run()
        try:
            pack = build_context_pack(run_dir)
            with open(os.path.join(pack, "REVIEW", "ai_maintenance_constraints.md"), "r", encoding="utf-8") as f:
                text = f.read()
            self.assertIn("Before modifying code", text)
            self.assertIn("human_review_required", text)
            self.assertIn("Do not assume missing evidence means absence of risk", text)
            self.assertIn("Re-run RepoSense", text)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

