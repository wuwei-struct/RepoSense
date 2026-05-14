import os
import sqlite3
import unittest
from reposense.scan import run_scan
from reposense.verifier import verify
def fixture_path(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
class VerifierMissingEvidenceTest(unittest.TestCase):
    def test_verify_fail_missing_evidence(self):
        rd = run_scan(fixture_path("repos", "api_json"), out_dir(), ruleset_dir(), budget_path())
        conn = sqlite3.connect(os.path.join(rd, "detections.sqlite"))
        c = conn.cursor()
        row = c.execute("select eid from evidence limit 1").fetchone()
        if row:
            c.execute("delete from evidence where eid=?", (row[0],))
            conn.commit()
        conn.close()
        res = verify(rd)
        self.assertFalse(res["ok"])
        self.assertTrue(any("missing" in e for e in res["errors"]))
