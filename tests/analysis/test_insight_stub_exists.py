import unittest

from reposense.analysis.reports.insight_stub import get_ai_insight_boundary_stub


class InsightStubExistsTest(unittest.TestCase):
    def test_stub_shape(self):
        obj = get_ai_insight_boundary_stub()
        self.assertTrue(isinstance(obj, dict))
        self.assertIn("included_in_oss", obj)
        self.assertIn("message", obj)
        self.assertEqual(obj.get("included_in_oss"), False)
        self.assertTrue("open-source engine" in str(obj.get("message") or ""))


if __name__ == "__main__":
    unittest.main()

