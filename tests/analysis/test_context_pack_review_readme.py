import json
import os
import shutil
import unittest

from reposense.context_pack import build_context_pack
from tests.analysis._context_pack_review_fixture import build_review_context_run


class ContextPackReviewReadmeTest(unittest.TestCase):
    def test_review_readme_map_and_root_readme(self):
        run_dir = build_review_context_run()
        try:
            pack = build_context_pack(run_dir)
            with open(os.path.join(pack, "REVIEW", "README.md"), "r", encoding="utf-8") as f:
                text = f.read()
            self.assertIn("Repository Review Context", text)
            self.assertIn("Recommended reading order", text)
            self.assertIn("This is not a correctness proof", text)
            with open(os.path.join(pack, "MAP", "index.json"), "r", encoding="utf-8") as f:
                idx = json.load(f)
            outputs = idx.get("outputs") or {}
            self.assertIn("review_section", outputs)
            self.assertIn("ai_maintenance_constraints", outputs)
            with open(os.path.join(pack, "README.md"), "r", encoding="utf-8") as f:
                root = f.read()
            self.assertIn("Repository Review Section", root)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

