import os
import unittest


class ReleaseDemoScriptExistsTest(unittest.TestCase):
    def test_release_demo_script_exists_and_has_canonical_path(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        p = os.path.join(root, "tools", "release_demo.ps1")
        self.assertTrue(os.path.isfile(p))
        with open(p, "r", encoding="utf-8") as f:
            txt = f.read()
        self.assertIn(".reposense_release_demo/current", txt)
        self.assertIn("demo_run.ps1", txt)


if __name__ == "__main__":
    unittest.main()
