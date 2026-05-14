import unittest
import os
import shutil
import tempfile
import sqlite3
from reposense.learn.site_builder import build_site

class LearnUISmokeTest(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.run_dir = tempfile.mkdtemp()
        # Mock concept graph
        self.cg_path = os.path.join(self.tmp_dir, "graph.json")
        with open(self.cg_path, "w") as f:
            f.write('{"concepts": [{"concept": "c1", "title": "Concept 1", "category": "cat1"}]}')
        
        # Mock sqlite
        conn = sqlite3.connect(os.path.join(self.run_dir, "detections.sqlite"))
        conn.execute("CREATE TABLE findings (fid TEXT, concept TEXT, rule_id TEXT, confidence REAL, primary_eid TEXT, meta_json TEXT)")
        conn.commit()
        conn.close()

    def tearDown(self):
        try:
            shutil.rmtree(self.tmp_dir)
            shutil.rmtree(self.run_dir)
        except:
            pass

    def test_learn_html_structure(self):
        build_site(run_dir=self.run_dir, out_dir=self.tmp_dir, concept_graph_path=self.cg_path)
        
        index_path = os.path.join(self.tmp_dir, "index.html")
        self.assertTrue(os.path.exists(index_path))
        
        with open(index_path, "r", encoding="utf-8") as f:
            html = f.read()
            
        # Check assets
        self.assertTrue(os.path.exists(os.path.join(self.tmp_dir, "assets", "reposense.css")))
        self.assertIn("href='assets/reposense.css'", html)
        
        # Check structure
        self.assertIn('class="topbar"', html)
        self.assertIn('class="concept-grid"', html)
        self.assertIn('class="concept-card"', html)

        # Check concept page
        concept_path = os.path.join(self.tmp_dir, "concepts", "c1.html")
        self.assertTrue(os.path.exists(concept_path))
        with open(concept_path, "r", encoding="utf-8") as f:
            c_html = f.read()
            self.assertIn('class="topbar"', c_html)
            self.assertIn('class="two-col-layout"', c_html)
            self.assertIn("href='../assets/reposense.css'", c_html)

if __name__ == '__main__':
    unittest.main()
