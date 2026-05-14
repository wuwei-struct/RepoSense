import os
import json
import tempfile
import unittest
from reposense.ci import run_ci
from reposense.verifier import verify


def _latest_run(out_dir):
    return sorted([os.path.join(out_dir, d) for d in os.listdir(out_dir) if d.startswith("run-")])[-1]


class JavaPr22IntegrationSmokeTest(unittest.TestCase):
    def _run_fixture(self, fixture):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", fixture))
        out = tempfile.mkdtemp(prefix=f"{fixture}_")
        code = run_ci(repo, out, profile="demo", with_context_pack=True, json_stdout=False)
        self.assertIn(code, (0, 2))
        rd = _latest_run(out)
        self.assertTrue(verify(rd, strict=True).get("ok"))
        return rd

    def test_java_kafka_min(self):
        rd = self._run_fixture("java_kafka_min")
        g = json.load(open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8"))
        qd = [n for n in (g.get("nodes") or []) if n.get("type") == "queue_dispatch" and (n.get("meta") or {}).get("language") == "java"]
        qc = [n for n in (g.get("nodes") or []) if n.get("type") == "queue_consume" and (n.get("meta") or {}).get("language") == "java"]
        self.assertGreaterEqual(len(qd), 1)
        self.assertGreaterEqual(len(qc), 1)

    def test_java_rabbit_min(self):
        rd = self._run_fixture("java_rabbit_min")
        g = json.load(open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8"))
        qd = [n for n in (g.get("nodes") or []) if n.get("type") == "queue_dispatch" and (n.get("meta") or {}).get("language") == "java"]
        qc = [n for n in (g.get("nodes") or []) if n.get("type") == "queue_consume" and (n.get("meta") or {}).get("language") == "java"]
        self.assertGreaterEqual(len(qd), 1)
        self.assertGreaterEqual(len(qc), 1)

    def test_java_jpa_mybatis_min(self):
        rd = self._run_fixture("java_jpa_mybatis_min")
        g = json.load(open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8"))
        db_nodes = [n for n in (g.get("nodes") or []) if n.get("type") == "db_op" and (n.get("meta") or {}).get("language") == "java"]
        db_read = [n for n in db_nodes if (n.get("meta") or {}).get("db.kind") == "db.read"]
        db_write = [n for n in db_nodes if (n.get("meta") or {}).get("db.kind") == "db.write"]
        self.assertGreaterEqual(len(db_read), 2)
        self.assertGreaterEqual(len(db_write), 2)

    def test_java_api_queue_db_closure_min(self):
        rd = self._run_fixture("java_api_queue_db_closure_min")
        g = json.load(open(os.path.join(rd, "event_graph.json"), "r", encoding="utf-8"))
        self.assertTrue(len(g.get("nodes") or []) > 0)
        self.assertTrue(any(n.get("type") == "api" and (n.get("meta") or {}).get("language") == "java" for n in (g.get("nodes") or [])))
        self.assertTrue(any(n.get("type") == "tx_boundary" and (n.get("meta") or {}).get("language") == "java" for n in (g.get("nodes") or [])))
        self.assertTrue(any(n.get("type") in ("queue_dispatch", "queue_consume") and (n.get("meta") or {}).get("language") == "java" for n in (g.get("nodes") or [])))
        self.assertTrue(any(n.get("type") == "db_op" and (n.get("meta") or {}).get("language") == "java" for n in (g.get("nodes") or [])))
        fw = json.load(open(os.path.join(rd, "context_pack", "ARTIFACTS", "framework_event_summary.json"), "r", encoding="utf-8"))
        self.assertIn("event_counts_by_framework", fw)
        self.assertTrue(os.path.isfile(os.path.join(rd, "exports", "context_pack.zip")))


if __name__ == "__main__":
    unittest.main()
