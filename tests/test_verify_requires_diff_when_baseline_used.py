import os
import json
import tempfile
import unittest
from reposense.verifier import verify


class VerifyRequiresDiffWhenBaselineUsedTest(unittest.TestCase):
    def test_verify_fails_without_diff(self):
        rd = tempfile.mkdtemp(prefix="verify_base_")
        # minimal required files
        os.makedirs(os.path.join(rd, "meta"), exist_ok=True)
        json.dump({"repo_root": rd}, open(os.path.join(rd, "manifest.json"), "w", encoding="utf-8"))
        json.dump({"engine_version":"0.1.0","ruleset_version":"1.0.0","budget_profile":"", "findings": [], "run_summary": {}}, open(os.path.join(rd, "report.json"), "w", encoding="utf-8"))
        open(os.path.join(rd, "report.html"), "w", encoding="utf-8").write("<html></html>")
        json.dump({"budget": {}}, open(os.path.join(rd, "meta","config.json"), "w", encoding="utf-8"))
        # required meta files
        os.makedirs(os.path.join(rd, "meta"), exist_ok=True)
        json.dump({"tool":"RepoSense"}, open(os.path.join(rd, "meta","tool_version.json"), "w", encoding="utf-8"))
        json.dump({"ruleset":"specs_v2"}, open(os.path.join(rd, "meta","ruleset_version.json"), "w", encoding="utf-8"))
        json.dump({}, open(os.path.join(rd, "event_graph.json"), "w", encoding="utf-8"))
        # sqlite DB with minimal schema
        import sqlite3
        sqlite3.connect(os.path.join(rd, "indices.sqlite")).close()
        con = sqlite3.connect(os.path.join(rd, "detections.sqlite"))
        cur = con.cursor()
        cur.execute("create table if not exists evidence (eid integer primary key, path text, start_line integer, end_line integer, snippet text, sha256 text, parse_level text)")
        cur.execute("create table if not exists findings (fid integer primary key, primary_eid integer)")
        cur.execute("create table if not exists finding_evidence (fid integer, eid integer)")
        cur.execute("create table if not exists events (type text, key text)")
        con.commit()
        con.close()
        # api_surface and entrypoints minimal
        json.dump({"endpoints": [], "stats": {}}, open(os.path.join(rd, "api_surface.json"), "w", encoding="utf-8"))
        json.dump({"entrypoints": []}, open(os.path.join(rd, "entrypoints.json"), "w", encoding="utf-8"))
        # gate baseline_used without diff
        json.dump({"baseline_used": True}, open(os.path.join(rd, "quality_gate.json"), "w", encoding="utf-8"))
        res = verify(rd)
        self.assertFalse(res.get("ok"))
        self.assertTrue(any("baseline_diff.json missing" in e for e in res.get("errors", [])))


if __name__ == "__main__":
    unittest.main()
