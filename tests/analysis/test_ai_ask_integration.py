import json
import os
import tempfile
import unittest

from reposense.analysis.ai.ask_export import export_ai_ask
from reposense.analysis.ai.pattern_export import export_patterns
from reposense.analysis.ai.risks_export import export_ai_risks
from reposense.analysis.ai.summary_export import export_ai_summary
from reposense.scan import run_scan


class AIAskIntegrationTest(unittest.TestCase):
    def test_ask_types_and_manifest(self):
        repo = tempfile.mkdtemp(prefix="repo_ask_int_")
        with open(os.path.join(repo, "app.py"), "w", encoding="utf-8") as f:
            f.write(
                "from fastapi import FastAPI\n"
                "app = FastAPI()\n"
                "@app.post('/orders')\n"
                "def create_order(payload):\n"
                "    save(payload)\n"
                "    send(payload)\n"
                "    return {'ok': True}\n"
            )
        out = tempfile.mkdtemp(prefix="out_ask_int_")
        rd = run_scan(
            repo,
            out,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rulesets", "specs_v2")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "presets", "prod_lite.json")),
        )
        export_patterns(rd)
        export_ai_summary(rd, write_json_file=True, write_markdown_file=True)
        export_ai_risks(rd)
        qs = [
            "这个系统主要做什么？",
            "这个系统最值得优先修复的风险是什么？",
            "为什么你说这里存在事务风险？证据是什么？",
            "订单路径里有没有 queue 和 db 写入？",
        ]
        for q in qs:
            res = export_ai_ask(rd, q, with_drilldown=True)
            self.assertTrue(os.path.isfile(res["json_path"]))
            self.assertTrue(os.path.isfile(res["markdown_path"]))
            with open(res["json_path"], "r", encoding="utf-8") as f:
                ans = json.load(f)
            self.assertIn(ans.get("question_type"), ("summary", "risk", "evidence", "flow", "unsupported"))
        with open(os.path.join(rd, "run_manifest.json"), "r", encoding="utf-8") as f:
            rm = json.load(f)
        paths = set([x.get("path") for x in (rm.get("artifacts") or [])])
        self.assertTrue(any(str(p).startswith("ai_ask/") and str(p).endswith("/answer.json") for p in paths))
        self.assertTrue(any(str(p).startswith("ai_ask/") and str(p).endswith("/answer.md") for p in paths))
