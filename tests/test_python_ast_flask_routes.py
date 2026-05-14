import os
import json
import tempfile
import unittest
from reposense.scan import run_scan


class PythonAstFlaskRoutesTest(unittest.TestCase):
    def test_flask_routes_detected(self):
        repo = tempfile.mkdtemp(prefix="py_flask_repo_")
        p = os.path.join(repo, "app.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write(
                "from flask import Flask\n"
                "app = Flask(__name__)\n"
                "@app.route('/hello')\n"
                "def hello():\n"
                "    return 'ok'\n"
                "@app.route('/pay', methods=['POST'])\n"
                "def pay():\n"
                "    return 'ok'\n"
            )
        out = tempfile.mkdtemp(prefix="run_py_ast_")
        rd = run_scan(repo, out, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2")), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json")))
        rep = json.load(open(os.path.join(rd, "report.json"), "r", encoding="utf-8"))
        api = [x for x in rep.get("findings", []) if x.get("concept") == "API"]
        self.assertTrue(len(api) >= 1)


if __name__ == "__main__":
    unittest.main()

