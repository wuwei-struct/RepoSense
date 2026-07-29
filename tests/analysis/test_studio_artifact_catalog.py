import unittest

from reposense.studio.artifact_catalog import (
    ARTIFACT_CATALOG,
    CATEGORY_GROUPS,
    validate_catalog,
)


class StudioArtifactCatalogTest(unittest.TestCase):
    def test_catalog_has_unique_safe_artifacts(self):
        self.assertEqual(validate_catalog(), [])
        artifact_ids = [item["artifact_id"] for item in ARTIFACT_CATALOG]
        self.assertEqual(len(artifact_ids), len(set(artifact_ids)))
        for item in ARTIFACT_CATALOG:
            self.assertFalse(item["relative_path"].startswith(("/", "\\")))
            self.assertNotIn("..", item["relative_path"].split("/"))

    def test_required_artifacts_and_groups_are_cataloged(self):
        paths = {item["relative_path"] for item in ARTIFACT_CATALOG}
        for path in [
            "report.html",
            "repository_review_report.md",
            "human_review_required.md",
            "transaction_correlation_summary.json",
            "typeorm_db_summary.json",
            "queue_reliability_summary.json",
            "exports/context_pack.zip",
            "context_pack/REVIEW/README.md",
        ]:
            self.assertIn(path, paths)
        labels = {item["display_name"] for item in CATEGORY_GROUPS}
        self.assertIn("Transactions & Database", labels)
        self.assertIn("Queue & Messaging Reliability", labels)
        self.assertIn("Advanced / Raw Artifacts", labels)


if __name__ == "__main__":
    unittest.main()
