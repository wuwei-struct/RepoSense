import os
import json
import tempfile
import unittest
from reposense.scan import run_scan


class PythonAstCeleryTest(unittest.TestCase):
    def test_celery_detected(self):
        repo = tempfile.mkdtemp(prefix="py_celery_repo_")
        p = os.path.join(repo, "tasks.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write(
                "from celery import shared_task\n"
                "@shared_task\n"
                "def add(x, y):\n"
                "    return x + y\n"
                "def kick():\n"
                "    add.delay(1, 2)\n"
            )
        out = tempfile.mkdtemp(prefix="run_py_ast_")
        rd = run_scan(repo, out, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rulesets', 'specs_v2')), os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'presets', 'prod_lite.json')))
        rep = json.load(open(os.path.join(rd, "report.json"), "r", encoding="utf-8"))
        q = [x for x in rep.get("findings", []) if x.get("concept") == "Queue"]
        self.assertTrue(len(q) >= 1)


if __name__ == "__main__":
    unittest.main()

