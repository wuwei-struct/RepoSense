import json
import os
import shutil
import unittest

from reposense.analysis.ai.pattern_rules import run_all_rules
from tests.analysis._transaction_correlation_fixture import build_transaction_run


class TransactionCorrelationPatternIntegrationTest(unittest.TestCase):
    def test_covered_is_suppressed_and_uncovered_keeps_callsite(self):
        run_dir = build_transaction_run()
        try:
            with open(os.path.join(run_dir, "patterns.json"), "r", encoding="utf-8") as handle:
                patterns = json.load(handle)["patterns"]
            outside = [row for row in patterns if row["pattern_type"] == "db_write_outside_tx"]
            files = {file for row in outside for file in row["files"]}
            self.assertNotIn("JpaCoveredRepository.java", files)
            target = next(row for row in outside if "JpaUncoveredRepository.java" in row["files"])
            self.assertEqual(target["status"], "confirmed")
            self.assertTrue(any(ref["file"] == "UncoveredService.java" for ref in target["evidence_refs"]))

            legacy = run_all_rules({
                "events": [{"event_id": "db", "type": "db_op", "meta": {"path": "Repo.java", "start_line": 4, "end_line": 4, "db.kind": "db.write", "language": "java"}}],
                "findings": [], "evidence_by_id": {},
            })
            self.assertEqual(next(row for row in legacy if row["pattern_type"] == "db_write_outside_tx")["status"], "confirmed")
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
