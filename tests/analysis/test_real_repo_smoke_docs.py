import os
import unittest


class RealRepoSmokeDocsTest(unittest.TestCase):
    def test_protocol_results_and_entrypoints_exist(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        protocol_path = os.path.join(root, "docs", "validation", "REAL_REPO_REVIEW_SMOKE.md")
        results_path = os.path.join(root, "docs", "validation", "REAL_REPO_REVIEW_RESULTS.md")
        self.assertTrue(os.path.isfile(protocol_path))
        self.assertTrue(os.path.isfile(results_path))
        with open(protocol_path, "r", encoding="utf-8") as handle:
            protocol = handle.read().lower()
        self.assertIn("does not run target repository code", protocol)
        self.assertIn("does not prove", protocol)
        self.assertIn("-allowNetwork".lower(), protocol)
        self.assertIn("triage-template.json", protocol)
        for rel in ["README.md", "README.zh-CN.md", os.path.join("docs", "INDEX.md")]:
            with open(os.path.join(root, rel), "r", encoding="utf-8") as handle:
                text = handle.read()
            self.assertIn("REAL_REPO_REVIEW_SMOKE.md", text)


if __name__ == "__main__":
    unittest.main()
