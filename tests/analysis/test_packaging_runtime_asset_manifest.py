import unittest
from pathlib import PurePosixPath

from reposense.runtime_resources import (
    resolve_runtime_resource,
    runtime_resource_manifest,
)


class PackagingRuntimeAssetManifestTest(unittest.TestCase):
    def test_manifest_is_stable_unique_and_complete(self):
        manifest = runtime_resource_manifest()
        ids = [item["resource_id"] for item in manifest]
        self.assertEqual(ids, [
            "studio_webui",
            "rulesets",
            "presets",
            "specs",
            "learn_concepts",
            "sqlite_schema",
        ])
        self.assertEqual(len(ids), len(set(ids)))
        for item in manifest:
            self.assertFalse(PurePosixPath(item["source_root"]).is_absolute())
            self.assertFalse(PurePosixPath(item["distribution_root"]).is_absolute())
            root = resolve_runtime_resource(item["resource_id"])
            for relative_path in item["required_files"]:
                self.assertTrue((root / relative_path).is_file(), relative_path)

    def test_manifest_excludes_non_runtime_content(self):
        serialized = repr(runtime_resource_manifest()).lower()
        for forbidden in (
            ".reposense_",
            ".tmp_",
            ".venv",
            "docs/",
            "screenshots",
            "tests/",
        ):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
