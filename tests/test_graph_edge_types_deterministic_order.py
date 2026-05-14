import os
import json
import tempfile
import unittest
from reposense.ci import run_ci


class GraphEdgeTypesDeterministicOrderTest(unittest.TestCase):
    def test_event_graph_stable(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "prod_suite", "python_api_tx_queue_cache_min"))
        out1 = tempfile.mkdtemp(prefix="graph_det_1_")
        out2 = tempfile.mkdtemp(prefix="graph_det_2_")
        code1 = run_ci(repo, out1, profile="prod_lite")
        code2 = run_ci(repo, out2, profile="prod_lite")
        self.assertIn(code1, (0,2))
        self.assertIn(code2, (0,2))
        rd1 = sorted([os.path.join(out1, d) for d in os.listdir(out1) if d.startswith("run-")])[-1]
        rd2 = sorted([os.path.join(out2, d) for d in os.listdir(out2) if d.startswith("run-")])[-1]
        g1 = open(os.path.join(rd1, "event_graph.json"), "rb").read()
        g2 = open(os.path.join(rd2, "event_graph.json"), "rb").read()
        self.assertEqual(g1, g2)


if __name__ == "__main__":
    unittest.main()
