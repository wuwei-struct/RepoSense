import os
import tempfile
import unittest

from reposense.studio.artifact_catalog import CATEGORY_GROUPS, build_artifact_presentation


def _url(run_id, path):
    return f"/runs/{run_id}/{path}"


class StudioArtifactGroupsTest(unittest.TestCase):
    def test_primary_artifacts_have_stable_order_and_only_real_urls(self):
        with tempfile.TemporaryDirectory() as td:
            for relative_path in [
                "repository_review_report.md",
                "human_review_required.md",
                "report.html",
                "context_pack/REVIEW/README.md",
                "queue_reliability_summary.json",
            ]:
                path = os.path.join(td, relative_path)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write("{}")
            presentation = build_artifact_presentation("run-one", td, _url)
            self.assertEqual(
                [item["artifact_id"] for item in presentation["recommended_artifacts"]],
                [
                    "repository_review_report",
                    "human_review_required",
                    "main_html_report",
                    "context_pack_review_readme",
                ],
            )
            available = [
                item
                for group in presentation["artifact_groups"]
                for item in group["artifacts"]
            ]
            self.assertTrue(all(item["available"] and item.get("url") for item in available))
            self.assertNotIn("TypeORM DB Summary", [item["display_name"] for item in available])

    def test_validation_group_expands_and_missing_is_not_zero(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "run_manifest.json"), "w", encoding="utf-8") as handle:
                handle.write("{}")
            presentation = build_artifact_presentation("run-two", td, _url)
            groups = {item["group_id"]: item for item in presentation["artifact_groups"]}
            self.assertTrue(groups["validation"]["default_expanded"])
            raw_group = next(item for item in CATEGORY_GROUPS if item["group_id"] == "advanced_raw")
            self.assertFalse(raw_group["default_expanded"])
            missing = {item["group_id"] for item in presentation["missing_capabilities"]}
            self.assertIn("messaging", missing)
            self.assertIn("transactions_database", missing)


if __name__ == "__main__":
    unittest.main()
