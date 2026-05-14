import os, unittest
def repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
class WorkflowTemplatePresentTest(unittest.TestCase):
    def test_template_contains_commands(self):
        p = os.path.join(repo_root(), ".github", "workflows", "reposense.yml.example")
        self.assertTrue(os.path.exists(p))
        with open(p, "r", encoding="utf-8") as f:
            txt = f.read()
        self.assertIn("reposense scan", txt)
        self.assertIn("export sarif", txt)
