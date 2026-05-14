import os
import unittest


class LanguageAdapterDocsExistTest(unittest.TestCase):
    def test_docs_exist(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.assertTrue(os.path.isfile(os.path.join(root, "docs", "EVENT_MODEL.md")))
        self.assertTrue(os.path.isfile(os.path.join(root, "docs", "LANGUAGE_ADAPTERS.md")))


if __name__ == "__main__":
    unittest.main()
