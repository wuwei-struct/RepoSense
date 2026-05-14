import os
import json
import tempfile
import sqlite3
import unittest
from reposense.verifier import run_verify


class VerifyRejectsUnknownEdgeTypeInStrictTest(unittest.TestCase):
    def test_unknown_edge_type_strict(self):
        rd = tempfile.mkdtemp(prefix="verify_edge_type_")
        os.makedirs(os.path.join(rd, "meta"), exist_ok=True)
        json.dump({"budget": {}, "repo_root": rd}, open(os.path.join(rd, "meta","config.json"), "w", encoding="utf-8"))
        json.dump({"findings": [], "run_summary": {}}, open(os.path.join(rd, "report.json"), "w", encoding="utf-8"))
        json.dump({"schema_version":1,"nodes":[{"event_id":"N1","type":"api","key":"GET /x","confidence":0.9,"meta":{}}],"edges":[{"edge_id":"E1","type":"unknown_new_edge","from":"N1","to":"N1","evidence":[],"meta":{}}]}, open(os.path.join(rd, "event_graph.json"), "w", encoding="utf-8"))
        # minimal sqlite
        con = sqlite3.connect(os.path.join(rd, "detections.sqlite"))
        cur = con.cursor()
        cur.execute("create table if not exists events (event_id text, type text, key text)")
        cur.execute("insert into events(event_id,type,key) values(?,?,?)", ("N1","api","GET /x"))
        cur.execute("create table if not exists evidence (eid integer primary key)")
        con.commit()
        con.close()
        json.dump({"version":"0.1.0"}, open(os.path.join(rd, "meta","tool_version.json"), "w", encoding="utf-8"))
        json.dump({"version":{"version":"1.0.0"}}, open(os.path.join(rd, "meta","ruleset_version.json"), "w", encoding="utf-8"))
        open(os.path.join(rd, "report.html"), "w", encoding="utf-8").write("<html></html>")
        with self.assertRaises(SystemExit) as cm:
            run_verify(rd, as_json=True, strict=True)
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
