import os
import unittest


class StudioWorkbenchDocsTest(unittest.TestCase):
    def test_workbench_documentation_and_index_exist(self):
        path = os.path.join("docs", "studio", "STUDIO_WORKBENCH.md")
        self.assertTrue(os.path.isfile(path))
        with open(path, "r", encoding="utf-8") as handle:
            workbench = handle.read()
        for marker in (
            "Quick Scan", "Full Repository Review", "Pipeline Progress",
            "available", "missing", "zero", "Public API privacy boundary",
            "does not prove",
        ):
            self.assertIn(marker, workbench)
        with open(os.path.join("docs", "INDEX.md"), "r", encoding="utf-8") as handle:
            self.assertIn("STUDIO_WORKBENCH.md", handle.read())

    def test_readmes_describe_review_workbench_without_release_claim(self):
        for name in ("README.md", "README.zh-CN.md"):
            with open(name, "r", encoding="utf-8") as handle:
                text = handle.read()
            self.assertIn("Full Repository Review", text)
            self.assertNotIn("v0.2.0 is now available", text)


if __name__ == "__main__":
    unittest.main()
