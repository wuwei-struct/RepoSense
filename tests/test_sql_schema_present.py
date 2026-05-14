import os
import sqlite3
import unittest
from reposense.scan import run_scan
def fixture_path(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
class SqlSchemaPresentTest(unittest.TestCase):
    def test_tables_present_and_version(self):
        rd = run_scan(fixture_path("repos", "api_json"), out_dir(), ruleset_dir(), budget_path())
        conn = sqlite3.connect(os.path.join(rd, "indices.sqlite"))
        c = conn.cursor()
        tables = set([r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()])
        for t in ["files","symbols","calls","text_hits","evidence","findings","finding_evidence","events","event_links"]:
            self.assertIn(t, tables)
        v = c.execute("PRAGMA user_version").fetchone()[0]
        self.assertEqual(v, 1)
        conn.close()
