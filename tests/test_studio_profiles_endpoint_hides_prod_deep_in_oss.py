import os
import unittest
from reposense.profiles import list_profiles


class StudioProfilesEndpointHidesProdDeepInOssTest(unittest.TestCase):
    def test_profiles_oss(self):
        os.environ["REPOSENSE_EDITION"] = "oss"
        lst = list_profiles(edition="oss")
        ids = [p["id"] for p in lst]
        self.assertNotIn("prod_deep", ids)


if __name__ == "__main__":
    unittest.main()
