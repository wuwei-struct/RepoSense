import os, json, sqlite3, unittest, tempfile, sys, subprocess
from ._mk_run_dir import mk_run_dir
def cg_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "learn", "graph", "concepts.json"))
class ExtractCasesTest(unittest.TestCase):
    def test_extract_two_findings(self):
        rd = mk_run_dir()
        conn = sqlite3.connect(os.path.join(rd, "detections.sqlite"))
        c = conn.cursor()
        # insert second evidence and finding
        c.execute("insert into evidence(eid,path,start_line,end_line,snippet,sha256,parse_level,node_type) values(2,?,?,?,?,'hash2','L2','')", ("schema.sql",1,1,"CREATE TABLE audit(id INT)"))
        meta2 = json.dumps({"table_names":["audit"]})
        c.execute("insert into findings(fid,concept,rule_id,confidence,primary_eid,meta_json) values(13,'Storage','L2_SQL_TABLE',0.9,2,?)", (meta2,))
        c.execute("insert into finding_evidence(fid,eid) values(13,2)")
        conn.commit()
        conn.close()
        outd = tempfile.mkdtemp(prefix="case-out-")
        cmd = [sys.executable, "-m", "reposense", "learn", "extract-cases", rd, "--out", outd, "--min-confidence", "0.0", "--graph", cg_path(), "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        self.assertEqual(res.returncode, 0)
        with open(os.path.join(outd, "casebank.jsonl"), "r", encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
        self.assertTrue(len(lines) >= 2)
        # stable case_id: same input re-run
        res2 = subprocess.run(cmd, stdout=subprocess.PIPE)
        with open(os.path.join(outd, "casebank.jsonl"), "r", encoding="utf-8") as f:
            lines2 = f.read().strip().splitlines()
        self.assertEqual(lines, lines2)
        for ln in lines:
            item = json.loads(ln)
            self.assertTrue("case_id" in item)
            self.assertTrue(len(item["evidence_refs"]) >= 1)
