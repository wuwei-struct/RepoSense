import unittest
from ._mk_run_dir import mk_run_dir
from reposense.learn.case_extractor import extract_cases
class CaseExtractorTest(unittest.TestCase):
    def test_extract_cases(self):
        rd = mk_run_dir()
        cases = extract_cases(rd)
        self.assertTrue(len(cases) >= 1)
        c = cases[0]
        self.assertTrue(len(c["evidence_refs"]) >= 1)
        self.assertEqual(list(c["notes"].keys()), ["meta_echo"])
