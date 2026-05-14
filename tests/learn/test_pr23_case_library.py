import os
import unittest
import tempfile
from reposense.learn.extract_cases import extract_cases_to_dir
from reposense.learn.concept_graph import default_concept_graph_path
from reposense.shared.case_library.store import CaseLibraryStore
from reposense.shared.case_library.schema import validate_case
from ._mk_run_dir_pr23 import mk_run_dir_pr23


class Pr23CaseLibraryTest(unittest.TestCase):
    def test_case_library_read_write(self):
        rd = mk_run_dir_pr23()
        outd = tempfile.mkdtemp(prefix="pr23-lib-")
        extract_cases_to_dir(rd, outd, 0.0, default_concept_graph_path(), as_json=False)
        store = CaseLibraryStore(outd)
        all_cases = store.list_cases()
        self.assertTrue(len(all_cases) >= 20)
        ids = set([(c.get("concept_id") or "").lower() for c in all_cases])
        self.assertIn("data.transaction_boundary", ids)
        self.assertIn("reliability.idempotency", ids)
        self.assertIn("concurrency.locking_or_guard", ids)
        for c in all_cases[:5]:
            v = validate_case(c, ids)
            self.assertTrue(v["ok"], msg=str(v["errors"]))
            self.assertTrue(len(c.get("evidence_refs") or []) >= 1)
        self.assertTrue(os.path.isfile(os.path.join(outd, "cases_index.json")))
        self.assertTrue(os.path.isdir(os.path.join(outd, "cases")))


if __name__ == "__main__":
    unittest.main()
