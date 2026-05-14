import os
import json
import unittest
import tempfile
from reposense.learn.extract_cases import extract_cases_to_dir
from reposense.learn.concept_graph import default_concept_graph_path
from ._mk_run_dir_pr23 import mk_run_dir_pr23


class Pr23ExtractCasesSmokeTest(unittest.TestCase):
    def test_stable_extract_and_counts(self):
        rd = mk_run_dir_pr23()
        outd = tempfile.mkdtemp(prefix="pr23-cases-")
        r1 = extract_cases_to_dir(rd, outd, 0.0, default_concept_graph_path(), as_json=True)
        idx1 = json.loads(open(os.path.join(outd, "cases_index.json"), "r", encoding="utf-8").read())
        sum1 = json.loads(open(os.path.join(outd, "extract_summary.json"), "r", encoding="utf-8").read())
        r2 = extract_cases_to_dir(rd, outd, 0.0, default_concept_graph_path(), as_json=True)
        idx2 = json.loads(open(os.path.join(outd, "cases_index.json"), "r", encoding="utf-8").read())
        sum2 = json.loads(open(os.path.join(outd, "extract_summary.json"), "r", encoding="utf-8").read())
        self.assertEqual(r1["counts"], r2["counts"])
        self.assertEqual(idx1, idx2)
        self.assertEqual(sum1, sum2)
        cc = sum1.get("concept_counts") or {}
        self.assertGreaterEqual(int(cc.get("data.transaction_boundary") or 0), 10)
        self.assertGreaterEqual(int(cc.get("reliability.idempotency") or 0), 5)
        self.assertGreaterEqual(int(cc.get("concurrency.locking_or_guard") or 0), 5)


if __name__ == "__main__":
    unittest.main()
