import os
import unittest


class ReleaseChecklistExistsTest(unittest.TestCase):
    def test_release_doc_exists(self):
        p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "RELEASE.md"))
        self.assertTrue(os.path.isfile(p))


if __name__ == "__main__":
    unittest.main()
