import os, unittest
from reposense.learn.concept_graph import load_concept_graph, validate_concept_graph, ConceptGraph
def cg_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "learn", "graph", "concepts.json"))
class ConceptGraphTest(unittest.TestCase):
    def test_concepts_valid(self):
        g = load_concept_graph(cg_path())
        v = validate_concept_graph(g)
        self.assertTrue(v["ok"])
        cg = ConceptGraph(g)
        self.assertTrue(len(cg.all_concepts()) >= 5)
