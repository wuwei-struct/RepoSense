import json
import os
import unittest

from tests._tmpdir import make_temp_dir
from tests.analysis._typeorm_fixture import FIXTURE, service_operations, write_minimal_run
from tools.validation.typeorm_db_validation import write_validation


class TypeOrmRealRepoValidationTest(unittest.TestCase):
    def test_validation_outputs_and_evidence(self):
        run_dir = make_temp_dir(prefix="typeorm_validation_")
        write_minimal_run(run_dir, service_operations())
        from reposense.analysis.db.typeorm_export import export_typeorm_db_operations
        export_typeorm_db_operations(run_dir)
        case_dir = make_temp_dir(prefix="typeorm_validation_case_")
        result = write_validation(run_dir, FIXTURE, case_id="fixture", case_dir=case_dir)
        self.assertEqual(result["summary"]["evidence_errors"], 0)
        self.assertTrue(os.path.isfile(os.path.join(case_dir, "typeorm_db_validation.md")))
        triage = json.load(open(os.path.join(case_dir, "typeorm_db_triage_template.json"), encoding="utf-8"))
        self.assertTrue(all(item["triage_status"] == "unreviewed" for item in triage["items"]))


if __name__ == "__main__":
    unittest.main()
