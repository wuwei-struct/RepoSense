import unittest
from reposense.linking.cross_language_matcher import match_callers_to_endpoints


class CrossLanguageMatcherTest(unittest.TestCase):
    def test_exact_and_template(self):
        callers = [
            {"caller_id": "c1", "language": "typescript", "http_method": "GET", "path_normalized": "/users/123", "file": "f.ts", "line_start": 1, "line_end": 1, "confidence": 0.9},
            {"caller_id": "c2", "language": "typescript", "http_method": "POST", "path_normalized": "/orders", "file": "f.ts", "line_start": 2, "line_end": 2, "confidence": 0.9},
        ]
        endpoints = [
            {"endpoint_id": "e1", "method": "GET", "path_normalized": "/users/{id}", "path": "/users/{id}", "language": "python", "file": "app.py", "line_start": 1, "line_end": 1, "evidence_ref": "E1"},
            {"endpoint_id": "e2", "method": "POST", "path_normalized": "/orders", "path": "/orders", "language": "python", "file": "app.py", "line_start": 2, "line_end": 2, "evidence_ref": "E2"},
        ]
        out = match_callers_to_endpoints(callers, endpoints)
        types = sorted([x["match_type"] for x in (out.get("links") or [])])
        self.assertIn("exact_match", types)
        self.assertIn("template_match", types)

    def test_method_mismatch_not_match(self):
        callers = [{"caller_id": "c1", "language": "typescript", "http_method": "GET", "path_normalized": "/orders", "file": "f.ts", "line_start": 1, "line_end": 1, "confidence": 0.9}]
        endpoints = [{"endpoint_id": "e1", "method": "POST", "path_normalized": "/orders", "path": "/orders", "language": "python", "file": "app.py", "line_start": 1, "line_end": 1, "evidence_ref": "E1"}]
        out = match_callers_to_endpoints(callers, endpoints)
        self.assertEqual(out.get("links"), [])
        self.assertEqual(len(out.get("unmatched_callers") or []), 1)


if __name__ == "__main__":
    unittest.main()
