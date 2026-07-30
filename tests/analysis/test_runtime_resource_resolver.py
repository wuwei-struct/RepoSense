import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from reposense import runtime_resources
from reposense.rules import load_ruleset
from reposense.specs import check_specs


class RuntimeResourceResolverTest(unittest.TestCase):
    def test_source_resources_are_complete_and_cwd_independent(self):
        before = Path.cwd()
        with tempfile.TemporaryDirectory(dir=".tmp_test_runs") as temp_dir:
            os.chdir(temp_dir)
            try:
                result = runtime_resources.validate_required_runtime_resources()
            finally:
                os.chdir(before)
        self.assertTrue(result["ok"], result)
        self.assertTrue(all(item["mode"] == "source" for item in result["resources"]))

    def test_concepts_are_valid_json(self):
        data = json.loads(
            runtime_resources.get_concepts_file().read_text(encoding="utf-8")
        )
        self.assertTrue(data.get("concepts"))

    def test_missing_installed_resource_does_not_fallback_elsewhere(self):
        with tempfile.TemporaryDirectory(dir=".tmp_test_runs") as temp_dir:
            with mock.patch.object(runtime_resources, "_SOURCE_ROOT", Path(temp_dir)):
                with mock.patch.object(
                    runtime_resources.metadata,
                    "distribution",
                    side_effect=runtime_resources.metadata.PackageNotFoundError,
                ):
                    with self.assertRaisesRegex(
                        runtime_resources.RuntimeResourceError,
                        "runtime resource 'rulesets'.*basic/rules.yaml",
                    ):
                        runtime_resources.get_rulesets_dir()

    def test_explicit_ruleset_and_specs_paths_remain_supported(self):
        with tempfile.TemporaryDirectory(dir=".tmp_test_runs") as temp_dir:
            temp = Path(temp_dir)
            ruleset = temp / "custom-ruleset"
            specs = temp / "custom-specs"
            shutil.copytree(runtime_resources.get_rulesets_dir() / "demo_v1", ruleset)
            shutil.copytree(runtime_resources.get_specs_dir(), specs)
            self.assertTrue(load_ruleset(str(ruleset))["rules"])
            self.assertTrue(check_specs(str(specs))["ok"])


if __name__ == "__main__":
    unittest.main()
