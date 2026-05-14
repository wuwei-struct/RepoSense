import os
import json
import tempfile
import unittest
from reposense.ci import run_ci


class GraphEdgeTypesSemanticPresentTest(unittest.TestCase):
    def test_semantic_edges_present(self):
        if os.environ.get("REPOSENSE_EDITION", "oss") != "enterprise":
            self.skipTest("enterprise only")
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "prod_suite", "python_api_tx_queue_cache_min"))
        out = tempfile.mkdtemp(prefix="graph_sem_")
        code = run_ci(repo, out, profile="prod_lite")
        self.assertIn(code, (0,2))
        runs = [os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")]
        rd = sorted(runs)[-1]
        g = json.load(open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8"))
        types = set([e.get("type") for e in (g.get("edges") or [])])
        self.assertTrue("encloses_tx" in types or "uses_cache" in types or "dispatches_job" in types)
        # check meta structure for one semantic edge
        sem = next((e for e in (g.get("edges") or []) if e.get("type") in ("encloses_tx","uses_cache","dispatches_job")), None)
        self.assertIsNotNone(sem)
        m = sem.get("meta") or {}
        self.assertTrue(isinstance(m.get("confidence"), (int,float)))
        self.assertTrue("reason" in m)
        self.assertTrue("scope_id" in m)
        self.assertTrue("span_overlap" in m)


if __name__ == "__main__":
    unittest.main()
