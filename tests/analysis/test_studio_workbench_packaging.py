import unittest
from zipfile import ZipFile

from reposense.runtime_resources import runtime_resource_manifest
from tools.release.package_runtime_smoke import build_wheel


class StudioWorkbenchPackagingTest(unittest.TestCase):
    ASSETS = {
        "app-shell.js",
        "app-shell.css",
        "analyze-form.js",
        "run-workbench.js",
    }

    def test_new_assets_are_required_runtime_resources(self):
        studio = next(
            item for item in runtime_resource_manifest()
            if item["resource_id"] == "studio_webui"
        )
        expected = {f"studio/{asset}" for asset in self.ASSETS}
        self.assertTrue(expected.issubset(set(studio["required_files"])))

    def test_new_assets_enter_the_wheel(self):
        _work_root, wheel_path, _result = build_wheel()
        with ZipFile(wheel_path) as archive:
            names = set(archive.namelist())
        for asset in self.ASSETS:
            self.assertIn(f"reposense-0.1.0.data/data/share/reposense/webui/studio/{asset}", names)


if __name__ == "__main__":
    unittest.main()
