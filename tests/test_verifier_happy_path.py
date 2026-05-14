import os
import json
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
class VerifierHappyPathTest(unittest.TestCase):
    def test_verify_ok(self):
        rd = run_scan(fixture_path("repos", "api_json"), out_dir(), ruleset_dir(), budget_path())
        res = verify(rd)
        self.assertTrue(res["ok"])
