import os
import json
import tempfile
import unittest
from reposense.scan import run_scan


class PythonAstCacheTest(unittest.TestCase):
    def test_cache_detected(self):
        repo = tempfile.mkdtemp(prefix="py_cache_repo_")
        p = os.path.join(repo, "cache_ops.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write(
                "from django.core.cache import cache\n"
                "def f():\n"
                "    cache.set('k','v')\n"
                "    cache.get('k')\n"
                "def g(redis_client):\n"
                "    redis_client.set('k','v')\n"
                "    redis_client.get('k')\n"
            )
        out = tempfile.mkdtemp(prefix="run_py_ast_")
        rd = run_scan(repo, out, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rulesets', 'specs_v2')), os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'presets', 'prod_lite.json')))
        rep = json.load(open(os.path.join(rd, "report.json"), "r", encoding="utf-8"))
        c = [x for x in rep.get("findings", []) if x.get("concept") == "Cache"]
        self.assertTrue(len(c) >= 1)


if __name__ == "__main__":
    unittest.main()

