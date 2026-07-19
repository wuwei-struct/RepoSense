import json
import os
import shutil
import unittest

from reposense.analysis.ai.pattern_engine import generate_patterns
from reposense.analysis.ai.pattern_rules import run_all_rules
from tests._tmpdir import make_temp_dir


class PatternEvidenceLocationsTest(unittest.TestCase):
    def setUp(self):
        self.run_dir = make_temp_dir(prefix="pattern_evidence_")
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "evidence_location_spring_min"))
        self.repo_root = root
        os.makedirs(os.path.join(self.run_dir, "evidence"))
        with open(os.path.join(self.run_dir, "manifest.json"), "w", encoding="utf-8") as handle:
            json.dump({"repo_root": root}, handle)
        with open(os.path.join(self.run_dir, "report.json"), "w", encoding="utf-8") as handle:
            json.dump({"findings": []}, handle)
        with open(os.path.join(self.run_dir, "cross_language_summary.json"), "w", encoding="utf-8") as handle:
            json.dump({}, handle)
        with open(os.path.join(self.run_dir, "cross_language_links.json"), "w", encoding="utf-8") as handle:
            json.dump({}, handle)

    def tearDown(self):
        shutil.rmtree(self.run_dir, ignore_errors=True)

    def test_db_write_uses_canonical_event_evidence_line(self):
        rel = "src/main/java/demo/PaymentRepository.java"
        source = os.path.join(self.repo_root, *rel.split("/"))
        with open(os.path.join(self.run_dir, "evidence", "E7.json"), "w", encoding="utf-8") as handle:
            json.dump({"path": source, "start_line": 7, "end_line": 7, "snippet": "entityManager.persist(new Object());"}, handle)
        graph = {
            "nodes": [
                {
                    "event_id": "db-event",
                    "type": "db_op",
                    "evidence": ["E7"],
                    "meta": {
                        "path": rel,
                        "scope": {"kind": "function", "name": "save", "start_line": 6, "end_line": 8},
                        "db.kind": "db.write",
                        "language": "java",
                        "framework": "jpa",
                    },
                }
            ],
            "edges": [],
        }
        with open(os.path.join(self.run_dir, "event_graph.json"), "w", encoding="utf-8") as handle:
            json.dump(graph, handle)

        patterns, _summary = generate_patterns(self.run_dir)
        target = next(item for item in patterns if item["pattern_type"] == "db_write_outside_tx")
        self.assertEqual(target["evidence_refs"][0]["file"], rel)
        self.assertEqual(target["evidence_refs"][0]["start_line"], 7)
        self.assertNotEqual(target["evidence_refs"][0]["start_line"], 0)

    def test_unknown_location_is_not_rewritten_to_first_line(self):
        patterns = run_all_rules(
            {
                "findings": [],
                "events": [
                    {
                        "event_id": "unknown-db",
                        "type": "db_op",
                        "evidence": ["E999"],
                        "meta": {"path": "src/main/java/demo/PaymentRepository.java", "db.kind": "db.write"},
                    }
                ],
                "evidence_by_id": {},
                "cross_language_summary": {},
                "cross_language_links": {},
            }
        )
        target = next(item for item in patterns if item["pattern_type"] == "db_write_outside_tx")
        self.assertEqual(target["evidence_refs"], [])
        self.assertEqual(target["status"], "suspected")
        self.assertIn("source_location_unavailable", target["metadata"]["limitations"])


if __name__ == "__main__":
    unittest.main()
