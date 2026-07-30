import unittest
from pathlib import Path

from tools.release.package_runtime_smoke import build_wheel, inspect_wheel


class WheelRuntimeAssetsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work_root = Path(".tmp_test_runs/temp/wheel_runtime_assets")
        _, cls.wheel, _ = build_wheel(cls.work_root)
        cls.result = inspect_wheel(cls.wheel)

    def test_wheel_contains_runtime_assets_and_license(self):
        self.assertEqual(self.result["wheel_version"], "0.1.0")
        self.assertEqual(self.result["missing_runtime_assets"], [])
        self.assertTrue(self.result["license_present"])
        self.assertGreaterEqual(self.result["runtime_asset_count"], 25)

    def test_wheel_excludes_local_and_test_content(self):
        self.assertEqual(self.result["forbidden_content"], [])
        names = self.result["archive_names"]
        self.assertFalse(any(name.startswith("tests/") for name in names))
        self.assertFalse(any(".reposense_" in name for name in names))
        self.assertFalse(any(".tmp_" in name for name in names))


if __name__ == "__main__":
    unittest.main()
