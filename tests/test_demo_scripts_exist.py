import os
import unittest


class DemoScriptsExistTest(unittest.TestCase):
    def test_scripts_exist(self):
        sh = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "demo_run.sh"))
        ps1 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "demo_run.ps1"))
        self.assertTrue(os.path.isfile(sh))
        self.assertTrue(os.path.isfile(ps1))
        txt = open(sh, "r", encoding="utf-8").read()
        self.assertIn("reposense ci run", txt)


if __name__ == "__main__":
    unittest.main()
