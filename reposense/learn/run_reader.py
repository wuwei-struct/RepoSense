import os
import json
import sqlite3
class RunHandle:
    def __init__(self, run_dir):
        self.run_dir = run_dir
        self.conn = sqlite3.connect(os.path.join(run_dir, "detections.sqlite"))
        self.conn.row_factory = sqlite3.Row
        self.manifest = {}
        self.meta = {}
        try:
            with open(os.path.join(run_dir, "manifest.json"), "r", encoding="utf-8") as f:
                self.manifest = json.load(f)
        except:
            self.manifest = {}
        try:
            with open(os.path.join(run_dir, "meta", "config.json"), "r", encoding="utf-8") as f:
                self.meta = json.load(f)
        except:
            self.meta = {}
    def iter_findings(self):
        rows = self.conn.cursor().execute("select fid, concept, rule_id, confidence, primary_eid, meta_json from findings").fetchall()
        items = []
        for r in rows:
            meta = {}
            try:
                meta = json.loads(r["meta_json"] or "{}")
            except:
                meta = {}
            items.append({"fid": r["fid"], "concept": r["concept"], "rule_id": r["rule_id"], "confidence": float(r["confidence"]), "primary_eid": r["primary_eid"], "meta": meta})
        return items
    def get_finding_evidence(self, fid):
        rows = self.conn.cursor().execute("select e.eid, e.path, e.start_line, e.end_line, e.snippet, e.sha256, e.parse_level, e.node_type from finding_evidence fe join evidence e on e.eid=fe.eid where fe.fid=?", (fid,)).fetchall()
        return [{"eid": f"E{r[0]}", "path": r[1], "start_line": r[2], "end_line": r[3], "snippet": r[4], "sha256": r[5], "parse_level": r[6], "node_type": r[7]} for r in rows]
    def iter_events(self):
        try:
            rows = self.conn.cursor().execute("select event_id, type, key, confidence, meta_json from events").fetchall()
        except Exception:
            return []
        out = []
        for r in rows:
            meta = {}
            try:
                meta = json.loads(r["meta_json"] or "{}")
            except:
                meta = {}
            out.append({"event_id": int(r["event_id"]), "type": str(r["type"] or ""), "key": str(r["key"] or ""), "confidence": float(r["confidence"] or 0.0), "meta": meta})
        return out
    def get_evidence(self, eid):
        p = os.path.join(self.run_dir, "evidence", f"E{eid}.json")
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    def close(self):
        try:
            self.conn.close()
        except:
            pass
def open_run(run_dir):
    return RunHandle(run_dir)
