import os
import shutil
import unittest

from tests._tmpdir import make_temp_dir
from tests.analysis._typescript_transaction_fixture import (
    build_typescript_transaction_run,
    fixture_repo,
)
from tools.validation.typescript_transaction_validation import write_validation


class TypeScriptTransactionRealRepoValidationTest(unittest.TestCase):
    def test_validation_outputs_and_evidence(self):
        run_dir = build_typescript_transaction_run()
        case_dir = make_temp_dir(prefix="typescript_transaction_case_")
        try:
            payload = write_validation(
                run_dir,
                fixture_repo(),
                case_id="fixture",
                case_dir=case_dir,
            )
            self.assertEqual(payload["summary"]["evidence_errors"], 0)
            self.assertEqual(payload["summary"]["duplicate_correlations"], 0)
            self.assertTrue(
                os.path.isfile(
                    os.path.join(
                        case_dir, "typescript_transaction_validation.md"
                    )
                )
            )
            self.assertTrue(
                os.path.isfile(
                    os.path.join(
                        case_dir,
                        "typescript_transaction_triage_template.json",
                    )
                )
            )
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)
            shutil.rmtree(case_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
