import os
import unittest


class StudioWorkbenchUiTest(unittest.TestCase):
    def setUp(self):
        self.root = os.path.join(os.getcwd(), "webui", "studio")

    def _read(self, name):
        with open(os.path.join(self.root, name), "r", encoding="utf-8") as handle:
            return handle.read()

    def test_index_is_a_shell_and_modules_are_separate(self):
        index = self._read("index.html")
        self.assertLess(len(index.splitlines()), 100)
        for asset in ("app-shell.css", "app-shell.js", "analyze-form.js", "run-workbench.js"):
            self.assertIn("/" + asset, index)
        self.assertNotIn("function render", index)
        self.assertNotIn("<style", index)

    def test_navigation_and_workbench_tabs_are_real(self):
        shell = self._read("app-shell.js")
        workbench = self._read("run-workbench.js")
        for marker in (
            "Home", "Analyze Repository", "Recent Runs", "Review Workspace",
            "Learn", "Documentation",
        ):
            self.assertIn(marker, shell)
        for marker in (
            "Overview", "Human Review", "Architecture & API",
            "Transactions & Database", "Queue & Cache", "Permission & AuthZ",
            "Code Health", "Validation", "Context Pack", "Artifacts",
        ):
            self.assertIn(marker, workbench)
        self.assertIn("StudioArtifactCards.render", workbench)


if __name__ == "__main__":
    unittest.main()
