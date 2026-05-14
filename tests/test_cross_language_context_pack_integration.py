import os
import json
import tempfile
import unittest
from reposense.ci import run_ci
from reposense.verifier import verify


def _latest_run(out):
    return sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]


class CrossLanguageContextPackIntegrationTest(unittest.TestCase):
    def _run_fixture(self, fixture):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", fixture))
        out = tempfile.mkdtemp(prefix=f"{fixture}_")
        code = run_ci(repo, out, profile="demo", with_context_pack=True, json_stdout=False)
        self.assertIn(code, (0, 2))
        rd = _latest_run(out)
        self.assertEqual(verify(rd, strict=True).get("ok"), True)
        return rd

    def _assert_cross_files(self, rd):
        self.assertTrue(os.path.isfile(os.path.join(rd, "api_callers.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "cross_language_links.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "cross_language_summary.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "context_pack", "ARTIFACTS", "api_callers.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "context_pack", "MAP", "cross_language_links.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "context_pack", "ARTIFACTS", "cross_language_summary.json")))
        rmd = open(os.path.join(rd, "context_pack", "README.md"), "r", encoding="utf-8").read()
        self.assertIn("Cross-language 摘要", rmd)

    def test_py_backend_ts_frontend(self):
        rd = self._run_fixture("py_backend_ts_frontend_min")
        self._assert_cross_files(rd)
        s = json.load(open(os.path.join(rd, "cross_language_summary.json"), "r", encoding="utf-8"))
        self.assertGreaterEqual(int(s.get("template_match_count") or 0), 1)
        self.assertGreaterEqual(int(s.get("exact_match_count") or 0), 1)

    def test_openapi_ts_client(self):
        rd = self._run_fixture("openapi_ts_client_min")
        self._assert_cross_files(rd)
        s = json.load(open(os.path.join(rd, "cross_language_summary.json"), "r", encoding="utf-8"))
        self.assertGreaterEqual(int(s.get("exact_match_count") or 0), 2)

    def test_ts_monorepo(self):
        rd = self._run_fixture("ts_monorepo_min")
        self._assert_cross_files(rd)
        links = json.load(open(os.path.join(rd, "cross_language_links.json"), "r", encoding="utf-8"))
        pairs = [x.get("language_pair") for x in (links.get("links") or [])]
        self.assertIn("typescript->typescript", pairs)
        self.assertTrue(os.path.isfile(os.path.join(rd, "exports", "context_pack.zip")))


if __name__ == "__main__":
    unittest.main()
