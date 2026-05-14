import os
import json
import sqlite3
import tempfile
import unittest
from reposense.scan import run_scan


class ProdSuiteEventRangesTest(unittest.TestCase):
    def test_event_ranges_and_graph(self):
        suite_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "prod_suite"))
        ruleset = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2"))
        budget = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json"))
        must_repo = "python_api_tx_queue_cache_min"
        out = tempfile.mkdtemp(prefix="run_events_")
        rd = run_scan(os.path.join(suite_root, must_repo), out, ruleset, budget)
        conn = sqlite3.connect(os.path.join(rd, "detections.sqlite"))
        c = conn.cursor()
        rows = c.execute("select type, count(1) from events group by type").fetchall()
        counts = {r[0]: r[1] for r in rows}
        conn.close()
        self.assertGreaterEqual(counts.get("tx_boundary", 0), 1)
        self.assertGreaterEqual(counts.get("queue_dispatch", 0), 1)
        self.assertGreaterEqual(counts.get("cache_op", 0), 1)
        with open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8") as f:
            g = json.load(f)
        types = {n.get("type") for n in g.get("nodes", [])}
        self.assertTrue({"api", "tx_boundary", "queue_dispatch", "cache_op"} <= types)
        edges = g.get("edges", [])
        self.assertTrue(any(e.get("type") == "observed_in_same_scope" for e in edges))


if __name__ == "__main__":
    unittest.main()
