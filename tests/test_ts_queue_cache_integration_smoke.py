import os
import json
import tempfile
import unittest
from reposense.ci import run_ci
from reposense.verifier import verify


def _latest_run(out):
    return sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]


class TsQueueCacheIntegrationSmokeTest(unittest.TestCase):
    def _run_repo(self, fixture):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", fixture))
        out = tempfile.mkdtemp(prefix=f"{fixture}_")
        code = run_ci(repo, out, profile="demo", with_context_pack=True, json_stdout=False)
        self.assertIn(code, (0, 2))
        rd = _latest_run(out)
        self.assertEqual(verify(rd, strict=True).get("ok"), True)
        return rd

    def test_bullmq_fixture(self):
        rd = self._run_repo("ts_bullmq_min")
        graph = json.load(open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8"))
        types = [n.get("type") for n in (graph.get("nodes") or [])]
        self.assertIn("queue_dispatch", types)
        self.assertIn("queue_consume", types)
        self.assertTrue(os.path.isfile(os.path.join(rd, "context_pack", "ARTIFACTS", "framework_event_summary.json")))

    def test_redis_fixture(self):
        rd = self._run_repo("ts_redis_min")
        graph = json.load(open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8"))
        cache_nodes = [n for n in (graph.get("nodes") or []) if n.get("type") == "cache_op"]
        self.assertTrue(len(cache_nodes) >= 3)
        self.assertTrue(os.path.isfile(os.path.join(rd, "context_pack", "ARTIFACTS", "framework_event_summary.json")))
        self.assertTrue(os.path.isfile(os.path.join(rd, "context_pack", "ARTIFACTS", "unsupported_detected.json")))

    def test_async_mix_fixture(self):
        rd = self._run_repo("ts_async_mix_min")
        caps = json.load(open(os.path.join(rd, "language_capabilities.json"), "r", encoding="utf-8"))
        self.assertIn("typescript", caps.get("detected_languages") or [])
        rmd = open(os.path.join(rd, "context_pack", "README.md"), "r", encoding="utf-8").read()
        self.assertIn("Queue events", rmd)
        self.assertIn("Cache events", rmd)
        self.assertTrue(os.path.isfile(os.path.join(rd, "exports", "context_pack.zip")))


if __name__ == "__main__":
    unittest.main()
