import os
import json
import tempfile
import unittest
from reposense.ci import run_ci
from reposense.verifier import verify


def _latest_run(out_dir):
    return sorted([os.path.join(out_dir, d) for d in os.listdir(out_dir) if d.startswith("run-")])[-1]


class JavaIntegrationSmokeTest(unittest.TestCase):
    def _run_fixture(self, fixture):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", fixture))
        out = tempfile.mkdtemp(prefix=f"{fixture}_")
        code = run_ci(repo, out, profile="demo", with_context_pack=True, json_stdout=False)
        self.assertIn(code, (0, 2))
        rd = _latest_run(out)
        self.assertTrue(verify(rd, strict=True).get("ok"))
        return rd

    def test_java_spring_routes_min(self):
        rd = self._run_fixture("java_spring_routes_min")
        surf = json.load(open(os.path.join(rd, "api_surface.json"), "r", encoding="utf-8"))
        eps = [e for e in (surf.get("endpoints") or []) if str((e.get("source") or {}).get("path") or "").lower().endswith(".java")]
        self.assertGreaterEqual(len(eps), 2)
        graph = json.load(open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8"))
        api_java = [n for n in (graph.get("nodes") or []) if n.get("type") == "api" and str((n.get("meta") or {}).get("language") or "") == "java"]
        self.assertGreaterEqual(len(api_java), 2)

    def test_java_transactional_min(self):
        rd = self._run_fixture("java_transactional_min")
        graph = json.load(open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8"))
        tx_java = [n for n in (graph.get("nodes") or []) if n.get("type") == "tx_boundary" and str((n.get("meta") or {}).get("language") or "") == "java"]
        self.assertGreaterEqual(len(tx_java), 2)

    def test_java_ts_cross_min(self):
        rd = self._run_fixture("java_ts_cross_min")
        cap = json.load(open(os.path.join(rd, "language_capabilities.json"), "r", encoding="utf-8"))
        self.assertIn("java", cap.get("registered_languages") or [])
        links = json.load(open(os.path.join(rd, "cross_language_links.json"), "r", encoding="utf-8"))
        pairs = [x.get("language_pair") for x in (links.get("links") or [])]
        self.assertIn("typescript->java", pairs)
        sm = json.load(open(os.path.join(rd, "cross_language_summary.json"), "r", encoding="utf-8"))
        self.assertGreaterEqual(int(sm.get("template_match_count") or 0), 1)
        self.assertGreaterEqual(int(sm.get("exact_match_count") or 0), 1)
        self.assertTrue(os.path.isfile(os.path.join(rd, "exports", "context_pack.zip")))


if __name__ == "__main__":
    unittest.main()
