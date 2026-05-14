import unittest
import os
import shutil
import tempfile
from reposense.report import build_report_html

class ReportUISmokeTest(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), "../tests/fixtures/repos/graph_mix")
        # We need a dummy report.json in tmp_dir
        with open(os.path.join(self.tmp_dir, "report.json"), "w") as f:
            f.write('{"findings": [{"fid": "F1", "concept": "test", "confidence": 1.0, "parse_level": "L1", "path": "foo.py", "start_line": 1, "end_line": 5, "snippet": "code"}]}')
        with open(os.path.join(self.tmp_dir, "event_graph.json"), "w") as f:
            f.write('{"nodes": [], "edges": []}')

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_report_html_structure(self):
        build_report_html(self.tmp_dir)
        
        report_path = os.path.join(self.tmp_dir, "report.html")
        self.assertTrue(os.path.exists(report_path))
        
        with open(report_path, "r", encoding="utf-8") as f:
            html = f.read()
            
        # Check assets
        self.assertTrue(os.path.exists(os.path.join(self.tmp_dir, "assets", "reposense.css")))
        self.assertIn("href='assets/reposense.css'", html)
        
        # Check structure
        self.assertIn('class="topbar"', html)
        self.assertIn('class="sidebar"', html)
        self.assertIn('class="details-pane hidden"', html)
        
        # Check JS
        self.assertIn('function switchView(view)', html)
        self.assertIn('function renderFindings(container)', html)

if __name__ == '__main__':
    unittest.main()
