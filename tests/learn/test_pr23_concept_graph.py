import unittest
from reposense.learn.concept_graph import load_concept_graph, ConceptGraph, default_concept_graph_path


class Pr23ConceptGraphTest(unittest.TestCase):
    def test_min_three_concepts_exist(self):
        g = load_concept_graph(default_concept_graph_path())
        cg = ConceptGraph(g)
        ids = set([(c.get("concept_id") or "").lower() for c in (g.get("concepts") or [])])
        self.assertIn("reliability.idempotency", ids)
        self.assertIn("data.transaction_boundary", ids)
        self.assertIn("concurrency.locking_or_guard", ids)
        self.assertEqual(len(ids), len(g.get("concepts") or []))
        for c in (g.get("concepts") or []):
            self.assertTrue(c.get("name"))
            self.assertTrue(c.get("summary"))
            self.assertTrue(isinstance(c.get("prerequisites") or [], list))
            self.assertTrue(isinstance(c.get("related") or [], list))
            self.assertTrue(isinstance(c.get("learning_objectives") or [], list))
            self.assertTrue(isinstance(c.get("anti_patterns") or [], list))
        self.assertIsNotNone(cg.get("data.transaction_boundary"))


if __name__ == "__main__":
    unittest.main()
