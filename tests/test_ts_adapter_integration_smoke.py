import os
import json
import tempfile
import unittest
from reposense.ci import run_ci
from reposense.verifier import verify


def _latest_run(out):
    return sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]


class TsAdapterIntegrationSmokeTest(unittest.TestCase):
    def test_ts_express_fixture(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "ts_express_min"))
        out = tempfile.mkdtemp(prefix="ts_expr_")
        code = run_ci(repo, out, profile="demo", with_context_pack=True, json_stdout=False)
        self.assertIn(code, (0, 2))
        rd = _latest_run(out)
        self.assertEqual(verify(rd, strict=True).get("ok"), True)
        graph = json.load(open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8"))
        self.assertTrue(len(graph.get("nodes") or []) > 0)
        api = json.load(open(os.path.join(rd, "api_surface.json"), "r", encoding="utf-8"))
        self.assertTrue(any("typescript" in str(ep.get("source_kind") or "") for ep in (api.get("endpoints") or [])))
        caps = json.load(open(os.path.join(rd, "language_capabilities.json"), "r", encoding="utf-8"))
        self.assertIn("typescript", caps.get("registered_languages") or [])
        self.assertIn("typescript", caps.get("detected_languages") or [])
        self.assertTrue(os.path.isfile(os.path.join(rd, "exports", "context_pack.zip")))

    def test_ts_nest_fixture(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "ts_nest_min"))
        out = tempfile.mkdtemp(prefix="ts_nest_")
        code = run_ci(repo, out, profile="demo", with_context_pack=True, json_stdout=False)
        self.assertIn(code, (0, 2))
        rd = _latest_run(out)
        self.assertEqual(verify(rd, strict=True).get("ok"), True)
        graph = json.load(open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8"))
        self.assertTrue(len(graph.get("nodes") or []) > 0)
        types = [n.get("type") for n in (graph.get("nodes") or [])]
        self.assertIn("api", types)
        self.assertIn("tx_boundary", types)
        caps = json.load(open(os.path.join(rd, "language_capabilities.json"), "r", encoding="utf-8"))
        self.assertIn("typescript", caps.get("detected_languages") or [])
        self.assertTrue(os.path.isfile(os.path.join(rd, "quality_gate.json")))


if __name__ == "__main__":
    unittest.main()
