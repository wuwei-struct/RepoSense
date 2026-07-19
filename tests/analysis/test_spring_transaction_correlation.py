import json
import os
import shutil
import unittest

from tests.analysis._transaction_correlation_fixture import build_transaction_run


class SpringTransactionCorrelationTest(unittest.TestCase):
    def test_method_class_uncovered_and_unknown(self):
        run_dir = build_transaction_run()
        try:
            with open(os.path.join(run_dir, "transaction_correlations.json"), "r", encoding="utf-8") as handle:
                rows = json.load(handle)["correlations"]
            by_file = {}
            for row in rows:
                by_file.setdefault(row["db_write_file"], []).append(row)
                for ref in row["transaction_evidence_refs"] + row["callsite_evidence_refs"] + row["db_write_evidence_refs"]:
                    self.assertFalse(os.path.isabs(ref["file"]))
                    self.assertGreaterEqual(ref["start_line"], 1)
            self.assertEqual(by_file["JpaCoveredRepository.java"][0]["coverage_status"], "covered_explicit")
            self.assertEqual(by_file["JpaClassCoveredRepository.java"][0]["coverage_status"], "covered_explicit")
            self.assertEqual(by_file["JpaClassCoveredRepository.java"][0]["transaction_scope"], "class")
            self.assertEqual(by_file["JpaUncoveredRepository.java"][0]["coverage_status"], "uncovered")
            self.assertEqual(by_file["JpaUnknownRepository.java"][0]["coverage_status"], "unknown")
            self.assertEqual(by_file["JpaUnknownRepository.java"][0]["callsite_line"], None)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
