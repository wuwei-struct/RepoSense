import os
import unittest


class PyprojectSetuptoolsExcludesRulesetsTest(unittest.TestCase):
    def test_pyproject_has_package_find(self):
        p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pyproject.toml"))
        self.assertTrue(os.path.isfile(p))
        txt = open(p, "r", encoding="utf-8").read()
        self.assertIn("[tool.setuptools.packages.find]", txt)
        self.assertIn("include = [\"reposense*", txt)
        self.assertTrue(("rulesets*" in txt))


if __name__ == "__main__":
    unittest.main()
