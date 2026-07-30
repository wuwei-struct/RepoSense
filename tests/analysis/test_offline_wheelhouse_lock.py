import json
import unittest
from pathlib import Path, PurePosixPath

from tools.release.offline_wheelhouse import (
    ALLOWED_PACKAGES,
    DEFAULT_LOCK,
    EXPECTED_DIRECT,
    OFFICIAL_INDEX,
    load_lock,
)


class OfflineWheelhouseLockTest(unittest.TestCase):
    def test_lock_is_platform_scoped_exact_and_safe(self):
        lock = load_lock(DEFAULT_LOCK)
        self.assertEqual(lock["schema_version"], 1)
        self.assertEqual(lock["target_python"], "3.11")
        self.assertEqual(lock["implementation"], "CPython")
        self.assertEqual(lock["platform"], "win32")
        self.assertEqual(lock["architecture"], "AMD64")
        self.assertEqual(lock["platform_tag"], "win-amd64")
        self.assertEqual(lock["repo_wheel_version"], "0.1.0")
        self.assertTrue(lock["forbidden_sdist"])
        self.assertEqual(lock["expected_source"], OFFICIAL_INDEX)

        packages = lock["packages"]
        names = [item["normalized_name"] for item in packages]
        self.assertEqual(names, sorted(ALLOWED_PACKAGES))
        self.assertEqual(len(names), len(set(names)))
        for item in packages:
            self.assertRegex(item["sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue(item["exact_version"])
            self.assertTrue(item["filename"].endswith(".whl"))
            self.assertFalse(PurePosixPath(item["filename"]).is_absolute())
            self.assertEqual(item["expected_source"], OFFICIAL_INDEX)
            expected_type = (
                "direct"
                if item["normalized_name"] in EXPECTED_DIRECT
                else "transitive"
            )
            self.assertEqual(item["dependency_type"], expected_type)

    def test_lock_has_no_machine_paths_or_volatile_fields(self):
        text = Path(DEFAULT_LOCK).read_text(encoding="utf-8")
        data = json.loads(text)
        serialized = json.dumps(data, sort_keys=True)
        self.assertNotRegex(serialized, r'(?i)(?:^|["\s])(?:[a-z]:[\\/]|\\\\)')
        self.assertNotRegex(serialized, r"(?i)(downloaded_at|generated_at|timestamp)")
        self.assertNotRegex(serialized, r"(?i)(username|home_directory)")


if __name__ == "__main__":
    unittest.main()
