import os
import unittest


class BaselineBranchPathsAreStableTest(unittest.TestCase):
    def test_path_string_stable(self):
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        main = os.path.join(base, ".github", "workflows", "reposense-main.yml")
        pr = os.path.join(base, ".github", "workflows", "reposense-pr.yml")
        main_text = open(main, "r", encoding="utf-8").read()
        pr_text = open(pr, "r", encoding="utf-8").read()
        self.assertIn("baselines/prod_lite/specs_v2/baseline.json", main_text)
        self.assertIn("baselines/prod_lite/specs_v2/baseline.json", pr_text)


if __name__ == "__main__":
    unittest.main()
