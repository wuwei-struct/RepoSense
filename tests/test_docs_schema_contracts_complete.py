import os
import unittest
from reposense.cli import json


class DocsSchemaContractsCompleteTest(unittest.TestCase):
    def test_all_contracts_exist(self):
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "schema"))
        req = ["report.json.md","event_graph.json.md","api_surface.json.md","entrypoints.json.md","coverage.json.md","quality_gate.json.md","ci_summary.json.md","run_manifest.json.md","baseline_in.json.md","baseline_diff.json.md","exports_report.sarif.json.md"]
        missing = [x for x in req if not os.path.isfile(os.path.join(base, x))]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
