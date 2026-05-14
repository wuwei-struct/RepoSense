import os
import json
import tempfile
import unittest
from reposense.scan import run_scan


class PythonAstDjangoAtomicTest(unittest.TestCase):
    def test_django_atomic_detected(self):
        repo = tempfile.mkdtemp(prefix="py_django_repo_")
        p = os.path.join(repo, "tx.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write(
                "from django.db import transaction\n"
                "def f():\n"
                "    with transaction.atomic():\n"
                "        pass\n"
            )
        out = tempfile.mkdtemp(prefix="run_py_ast_")
        rd = run_scan(repo, out, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2")), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json")))
        rep = json.load(open(os.path.join(rd, "report.json"), "r", encoding="utf-8"))
        tx = [x for x in rep.get("findings", []) if x.get("concept") == "Transaction"]
        self.assertTrue(len(tx) >= 1)


if __name__ == "__main__":
    unittest.main()

