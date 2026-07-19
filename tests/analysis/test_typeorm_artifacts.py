import json
import os
import unittest

from reposense.analysis.db.typeorm_export import export_typeorm_db_operations
from reposense.analysis.reports.backend_verifier_report import (
    generate_backend_verifier_report,
)
from reposense.analysis.review.review_engine import generate_repository_review
from reposense.context_pack import build_context_pack
from reposense.run_manifest import build_run_manifest
from tests._tmpdir import make_temp_dir
from tests.analysis._typeorm_fixture import service_operations, write_minimal_run


class TypeOrmArtifactsTest(unittest.TestCase):
    def test_manifest_context_pack_and_summary(self):
        run_dir = make_temp_dir(prefix="typeorm_artifacts_")
        write_minimal_run(run_dir, service_operations())
        result = export_typeorm_db_operations(run_dir)
        self.assertGreater(result["summary"]["db_reads"], 0)
        backend = generate_backend_verifier_report(run_dir)
        self.assertEqual(
            backend["typeorm_db_coverage"]["db_reads"],
            result["summary"]["db_reads"],
        )
        review = generate_repository_review(run_dir)
        self.assertEqual(
            review["transaction_review"]["typeorm_db_coverage"]["status"],
            "enabled",
        )
        build_context_pack(run_dir)
        manifest = build_run_manifest(run_dir)
        paths = {item["path"] for item in manifest["artifacts"]}
        self.assertIn("typeorm_db_operations.json", paths)
        self.assertIn("context_pack/ARTIFACTS/typeorm_db_summary.json", paths)
        index = json.load(open(os.path.join(run_dir, "context_pack", "MAP", "index.json"), encoding="utf-8"))
        self.assertIn("typeorm_db_operations", index["outputs"])


if __name__ == "__main__":
    unittest.main()
