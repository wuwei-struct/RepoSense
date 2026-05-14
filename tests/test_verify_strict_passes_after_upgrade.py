import os
import json
import tempfile
import sqlite3
import unittest
from reposense.run_upgrade import upgrade_run
from reposense.verifier import run_verify


class VerifyStrictPassesAfterUpgradeTest(unittest.TestCase):
    def test_strict_pass(self):
        rd = tempfile.mkdtemp(prefix="upgrade_strict_")
        os.makedirs(os.path.join(rd, "meta"), exist_ok=True)
        json.dump({"budget": {}, "ruleset_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2"))}, open(os.path.join(rd, "meta","config.json"), "w", encoding="utf-8"))
        json.dump({"findings":[],"run_summary":{}}, open(os.path.join(rd, "report.json"), "w", encoding="utf-8"))
        json.dump({"nodes":[],"edges":[]}, open(os.path.join(rd, "event_graph.json"), "w", encoding="utf-8"))
        json.dump({"endpoints":[],"stats":{},"mismatches":{}}, open(os.path.join(rd, "api_surface.json"), "w", encoding="utf-8"))
        json.dump({"entrypoints":[],"stats":{}}, open(os.path.join(rd, "entrypoints.json"), "w", encoding="utf-8"))
        json.dump({"walk":{},"warnings":[]}, open(os.path.join(rd, "coverage.json"), "w", encoding="utf-8"))
        open(os.path.join(rd, "report.html"), "w", encoding="utf-8").write("<html></html>")
        json.dump({"version":"0.1.0"}, open(os.path.join(rd, "meta","tool_version.json"), "w", encoding="utf-8"))
        json.dump({"version":{"version":"1.0.0"}}, open(os.path.join(rd, "meta","ruleset_version.json"), "w", encoding="utf-8"))
        # sqlite minimal
        sqlite3.connect(os.path.join(rd, "indices.sqlite")).close()
        con = sqlite3.connect(os.path.join(rd, "detections.sqlite"))
        cur = con.cursor()
        cur.execute("create table if not exists evidence (eid integer primary key, path text, start_line integer, end_line integer, snippet text, sha256 text, parse_level text)")
        cur.execute("create table if not exists findings (fid integer primary key, primary_eid integer)")
        cur.execute("create table if not exists finding_evidence (fid integer, eid integer)")
        cur.execute("create table if not exists events (type text, key text)")
        con.commit()
        con.close()
        # upgrade then strict verify
        code = upgrade_run(rd, inplace=True)
        self.assertEqual(code, 0)
        try:
            run_verify(rd, as_json=True, strict=True)
        except SystemExit as e:
            self.assertEqual(e.code, 0)


if __name__ == "__main__":
    unittest.main()
