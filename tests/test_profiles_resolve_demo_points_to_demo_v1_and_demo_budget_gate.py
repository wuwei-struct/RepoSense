import os
import unittest
from reposense.profiles import resolve_profile


class ProfilesResolveDemoPointsTest(unittest.TestCase):
    def test_demo_points(self):
        os.environ["REPOSENSE_EDITION"] = "oss"
        p = resolve_profile("demo", edition="oss")
        self.assertTrue(p["ruleset_dir"].endswith(os.path.join("rulesets","demo_v1")))
        self.assertTrue(p["budget_path"].endswith(os.path.join("presets","demo.json")))
        self.assertTrue(p["gate_path"].endswith(os.path.join("presets","gates","demo.json")))


if __name__ == "__main__":
    unittest.main()
