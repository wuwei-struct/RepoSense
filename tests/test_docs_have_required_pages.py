import os
import unittest


class DocsHaveRequiredPagesTest(unittest.TestCase):
    def test_docs_exist(self):
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
        req = ["what-is-reposense.md","artifacts-five-pack.md","ci-baseline-gate.md"]
        for r in req:
            self.assertTrue(os.path.isfile(os.path.join(base, r)))


if __name__ == "__main__":
    unittest.main()
