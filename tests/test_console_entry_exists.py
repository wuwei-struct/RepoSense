import os, unittest
class ConsoleEntryExistsTest(unittest.TestCase):
    def test_pyproject_has_entry(self):
        p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pyproject.toml"))
        self.assertTrue(os.path.exists(p))
        with open(p, "r", encoding="utf-8") as f:
            txt = f.read()
        self.assertIn("project.scripts", txt)
        self.assertIn("reposense = \"reposense.cli:main\"", txt)
