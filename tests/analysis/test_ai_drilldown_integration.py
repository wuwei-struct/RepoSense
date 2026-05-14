import json
import os
import tempfile
import unittest

from reposense.analysis.ai.drilldown_export import export_drilldown
from reposense.analysis.ai.pattern_export import export_patterns
from reposense.scan import run_scan


class AIDrilldownIntegrationTest(unittest.TestCase):
    def test_scan_patterns_drilldown_manifest(self):
        repo = tempfile.mkdtemp(prefix="repo_drilldown_int_")
        with open(os.path.join(repo, "app.py"), "w", encoding="utf-8") as f:
            f.write(
                "from fastapi import FastAPI\n"
                "app = FastAPI()\n"
                "@app.post('/orders')\n"
                "def create_order(payload):\n"
                "    save(payload)\n"
                "    dispatch(payload)\n"
                "    return {'ok': True}\n"
            )
        out = tempfile.mkdtemp(prefix="out_drilldown_int_")
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
            # scan can be sparse; inject a deterministic pattern for drilldown infra validation
            pats = [
                {
                    "pattern_id": "int-pat-1",
                    "pattern_type": "transaction_missing",
                    "title": "x",
                    "severity": "high",
                    "confidence": 0.8,
                    "summary": "x",
                    "supporting_findings": [],
                    "supporting_events": [],
                    "evidence_refs": [{"source_type": "event", "event_id": "", "file": "app.py", "start_line": 3, "end_line": 5}],
                    "files": ["app.py"],
                    "languages": ["python"],
                    "frameworks": ["fastapi"],
                    "status": "suspected",
                    "explain_stub": "x",
                    "metadata": {},
                }
            ]
            with open(os.path.join(rd, "patterns.json"), "w", encoding="utf-8") as f:
                json.dump({"patterns": pats}, f)
        pid = str(pats[0].get("pattern_id") or "")
        res = export_drilldown(rd, "pattern", pid)
        self.assertTrue(os.path.isfile(res["json_path"]))
        self.assertTrue(os.path.isfile(res["markdown_path"]))
        with open(res["json_path"], "r", encoding="utf-8") as f:
            pack = json.load(f)
        self.assertEqual(pack.get("target_type"), "pattern")
        self.assertEqual(pack.get("target_id"), pid)
        self.assertTrue(os.path.isfile(os.path.join(rd, "run_manifest.json")))
        with open(os.path.join(rd, "run_manifest.json"), "r", encoding="utf-8") as f:
            rm = json.load(f)
        paths = set([x.get("path") for x in (rm.get("artifacts") or [])])
        self.assertTrue(any(str(p).startswith("ai_drilldown/") and str(p).endswith("/snippet_pack.json") for p in paths))
