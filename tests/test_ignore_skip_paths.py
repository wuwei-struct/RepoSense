import unittest
from reposense.utils import is_ignored


class IgnoreSkipPathsTest(unittest.TestCase):
    def test_skip_dict_and_csv(self):
        self.assertTrue(is_ignored("assets/dict_source/cedict.csv"))
        self.assertTrue(is_ignored("data/large/file.csv"))
        self.assertTrue(is_ignored("static/images/logo.png"))
        self.assertTrue(is_ignored("packs/context/out.zip"))
    def test_allow_code(self):
        self.assertFalse(is_ignored("src/index.ts"))
        self.assertFalse(is_ignored("app/main.py"))
        self.assertFalse(is_ignored("service/worker.go"))


if __name__ == "__main__":
    unittest.main()

