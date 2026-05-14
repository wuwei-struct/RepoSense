import unittest

from reposense.analysis.ai.drilldown_schema import build_request, normalize_budget, normalize_snippet_pack


class DrilldownSchemaTest(unittest.TestCase):
    def test_request_schema_and_stable_id(self):
        a = build_request("pattern", "p1", {"context_lines": 30})
        b = build_request("pattern", "p1", {"context_lines": 30})
        self.assertEqual(a["request_id"], b["request_id"])
        self.assertEqual(a["target_type"], "pattern")
        self.assertEqual(a["target_id"], "p1")

    def test_budget_normalization(self):
        b = normalize_budget({"max_files": "2", "max_snippets": 0})
        self.assertEqual(b["max_files"], 2)
        self.assertEqual(b["max_snippets"], 1)

    def test_pack_normalization(self):
        pack = normalize_snippet_pack(
            {
                "request_id": "dd-1",
                "run_dir": "x",
                "target_type": "finding",
                "target_id": "f1",
                "selected_snippets": [
                    {
                        "snippet_id": "s1",
                        "file": "a.py",
                        "line_start": 1,
                        "line_end": 2,
                        "snippet": "x",
                        "source_refs": [{"finding_id": "f1", "source_type": "finding"}],
                    }
                ],
                "budget": {"max_files": 2, "total_chars": 10},
                "selection_trace": {"k": 1},
                "limitations": ["l1"],
            }
        )
        self.assertEqual(pack["source_mode"], "facts_first_drilldown")
        self.assertEqual(pack["selected_files"], ["a.py"])
        self.assertEqual(pack["budget"]["total_chars"], 10)

