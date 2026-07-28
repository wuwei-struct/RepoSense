import os
import unittest


class RuntimeArchivePathsTest(unittest.TestCase):
    def setUp(self):
        self.root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def _read(self, relative_path):
        with open(os.path.join(self.root, relative_path), "r", encoding="utf-8") as handle:
            return handle.read()

    def test_runtime_archives_stay_under_ignored_roots(self):
        expectations = {
            "tools/review_demo.ps1": (
                '$historyRoot = Join-Path $canonicalRoot "history"',
                ".reposense_review_demo",
            ),
            "tools/release_demo.ps1": (
                '$historyRoot = Join-Path $canonicalRoot "history"',
                ".reposense_release_demo",
            ),
            "tools/real_repo_review_smoke.ps1": (
                '$historyRoot = Join-Path $smokeRoot "history"',
                ".reposense_real_repo_smoke",
            ),
        }
        for relative_path, markers in expectations.items():
            text = self._read(relative_path)
            with self.subTest(script=relative_path):
                self.assertIn(markers[0], text)
                self.assertIn(markers[1], text)
                self.assertIn("Move-Item -LiteralPath", text)
                self.assertNotIn("docs\\archive\\local-artifacts\\root-moved", text)
                self.assertNotIn("MOVED_FROM_ROOT.md", text)

    def test_runtime_roots_are_ignored(self):
        ignore_text = self._read(".gitignore")
        for runtime_root in (
            ".reposense_review_demo/",
            ".reposense_release_demo/",
            ".reposense_real_repo_smoke/",
        ):
            self.assertIn(runtime_root, ignore_text)


if __name__ == "__main__":
    unittest.main()
