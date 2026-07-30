import unittest
from pathlib import Path

from tools.release.package_runtime_smoke import run_package_runtime_smoke


class InstalledTargetRuntimeSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = run_package_runtime_smoke(
            Path(".tmp_test_runs/temp/installed_target_runtime_smoke")
        )

    def test_target_package_and_resources_are_installed(self):
        self.assertEqual(self.summary["asset_packaging"], "pass")
        self.assertEqual(self.summary["target_install_smoke"], "pass")
        self.assertEqual(
            self.summary["target"]["target_package_import"],
            "reposense/__init__.py",
        )
        validation = self.summary["target"]["resource_validation"]
        self.assertTrue(validation["ok"], validation)
        self.assertTrue(
            all(item["mode"] == "installed" for item in validation["resources"])
        )

    def test_installed_cli_studio_learn_specs_and_ci(self):
        target = self.summary["target"]
        self.assertEqual(target["cli_help_commands"], 6)
        self.assertGreater(target["concept_count"], 0)
        self.assertTrue(target["specs_ok"])
        self.assertEqual(target["ci_gate_status"], "pass")
        self.assertTrue(all(code == 200 for code in target["studio_http"].values()))

    def test_fresh_venv_gate_is_not_overstated(self):
        self.assertEqual(self.summary["fresh_venv_offline_smoke"], "pending")
        self.assertIn(
            "fresh_venv_offline_dependency_smoke_pending",
            self.summary["warnings"],
        )


if __name__ == "__main__":
    unittest.main()
