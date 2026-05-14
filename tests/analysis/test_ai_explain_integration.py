import json
import os
import tempfile
import unittest

from reposense.analysis.ai.explain_export import export_ai_explain
from reposense.analysis.ai.pattern_export import export_patterns
from reposense.scan import run_scan


class AIExplainIntegrationTest(unittest.TestCase):
    def test_explain_outputs_and_manifest(self):
        repo = tempfile.mkdtemp(prefix="repo_explain_int_")
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
        out = tempfile.mkdtemp(prefix="out_explain_int_")
        rd = run_scan(
            repo,
            out,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rulesets", "specs_v2")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "presets", "prod_lite.json")),
        )
        pres = export_patterns(rd)
        with open(pres["patterns_path"], "r", encoding="utf-8") as f:
            pats = json.load(f).get("patterns") or []
        if not pats:
            pats = [
                {
                    "pattern_id": "ep-confirmed",
                    "pattern_type": "queue_without_consumer",
                    "title": "x",
                    "severity": "medium",
                    "confidence": 0.8,
                    "summary": "x",
                    "supporting_findings": [],
                    "supporting_events": [],
                    "evidence_refs": [{"source_type": "event", "file": "app.py", "start_line": 5, "end_line": 5}],
                    "files": ["app.py"],
                    "languages": ["python"],
                    "frameworks": ["fastapi"],
                    "status": "confirmed",
                    "explain_stub": "x",
                    "metadata": {},
                },
                {
                    "pattern_id": "ep-suspected",
                    "pattern_type": "api_write_without_idempotency_guard",
                    "title": "x",
                    "severity": "medium",
                    "confidence": 0.6,
                    "summary": "x",
                    "supporting_findings": [],
                    "supporting_events": [],
                    "evidence_refs": [{"source_type": "event", "file": "app.py", "start_line": 4, "end_line": 6}],
                    "files": ["app.py"],
                    "languages": ["python"],
                    "frameworks": ["fastapi"],
                    "status": "suspected",
                    "explain_stub": "x",
                    "metadata": {},
                },
            ]
            with open(os.path.join(rd, "patterns.json"), "w", encoding="utf-8") as f:
                json.dump({"patterns": pats}, f)
        confirmed_id = str((next((p for p in pats if str(p.get("status") or "") == "confirmed"), pats[0])).get("pattern_id") or "")
        suspected_id = str((next((p for p in pats if str(p.get("status") or "") == "suspected"), pats[0])).get("pattern_id") or "")

        a = export_ai_explain(rd, "pattern", confirmed_id, no_drilldown=True)
        b = export_ai_explain(rd, "pattern", suspected_id, with_drilldown=True)
        self.assertTrue(os.path.isfile(a["json_path"]))
        self.assertTrue(os.path.isfile(a["markdown_path"]))
        self.assertTrue(os.path.isfile(b["json_path"]))
        self.assertTrue(os.path.isfile(b["markdown_path"]))
        self.assertIn((b["result"] or {}).get("mode"), ("facts_plus_drilldown", "facts_only"))
        self.assertTrue(os.path.isfile(os.path.join(rd, "run_manifest.json")))
        with open(os.path.join(rd, "run_manifest.json"), "r", encoding="utf-8") as f:
            rm = json.load(f)
        paths = set([x.get("path") for x in (rm.get("artifacts") or [])])
        self.assertTrue(any(str(x).startswith("ai_explain/") and str(x).endswith("/explain.json") for x in paths))
        self.assertTrue(any(str(x).startswith("ai_explain/") and str(x).endswith("/explain.md") for x in paths))
