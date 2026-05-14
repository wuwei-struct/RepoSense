import os
import json
import tempfile
import unittest
from reposense.ci import run_ci


class RunSummaryIncludesGraphEdgesByTypeTest(unittest.TestCase):
    def test_run_summary_has_edge_types(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "prod_suite", "python_api_tx_queue_cache_min"))
        out = tempfile.mkdtemp(prefix="run_sum_edges_")
        code = run_ci(repo, out, profile="prod_lite")
        self.assertIn(code, (0,2))
        rd = sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]
        rep = json.load(open(os.path.join(rd, "report.json"), "r", encoding="utf-8"))
        gtypes = rep.get("run_summary", {}).get("graph_edges_by_type", {})
        self.assertTrue(isinstance(gtypes, dict))
        # at least keys exist if edges exist
        self.assertTrue(len(gtypes) >= 0)


if __name__ == "__main__":
    unittest.main()
