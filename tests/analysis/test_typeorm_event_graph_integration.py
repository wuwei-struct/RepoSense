import json
import os
import unittest

from reposense.ci import run_ci
from tests._tmpdir import make_temp_dir
from tests.analysis._typeorm_fixture import FIXTURE


class TypeOrmEventGraphIntegrationTest(unittest.TestCase):
    def test_ci_run_emits_typeorm_graph_and_artifacts(self):
        out = make_temp_dir(prefix="typeorm_graph_")
        code = run_ci(str(FIXTURE), out, profile="demo")
        self.assertEqual(code, 0)
        run_dir = max(
            (os.path.join(out, name) for name in os.listdir(out) if name.startswith("run-")),
            key=os.path.getmtime,
        )
        graph = json.load(open(os.path.join(run_dir, "event_graph.json"), encoding="utf-8"))
        nodes = [node for node in graph["nodes"] if (node.get("meta") or {}).get("framework") == "typeorm"]
        self.assertTrue(any((node.get("meta") or {}).get("db.kind") == "db.read" for node in nodes))
        self.assertTrue(any((node.get("meta") or {}).get("db.kind") == "db.write" for node in nodes))
        self.assertTrue(os.path.isfile(os.path.join(run_dir, "typeorm_db_operations.json")))


if __name__ == "__main__":
    unittest.main()
