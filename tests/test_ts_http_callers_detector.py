import unittest
from reposense.parsers.ts_http_callers import detect_ts_http_callers


class TsHttpCallersDetectorTest(unittest.TestCase):
    def test_fetch_and_method(self):
        lines = ['fetch("/users/1")', 'fetch("/orders", { method: "POST" })']
        data = detect_ts_http_callers("a.ts", lines)
        callers = data.get("callers") or []
        keys = sorted([(c["http_method"], c["path_normalized"]) for c in callers])
        self.assertIn(("GET", "/users/1"), keys)
        self.assertIn(("POST", "/orders"), keys)

    def test_axios_verbs(self):
        lines = ['axios.get("/a")', 'axios.post("/b")', 'axios.put("/c")', 'axios.delete("/d")', 'axios.patch("/e")']
        data = detect_ts_http_callers("a.ts", lines)
        verbs = sorted([c["http_method"] for c in (data.get("callers") or [])])
        self.assertEqual(verbs, ["DELETE", "GET", "PATCH", "POST", "PUT"])

    def test_dynamic_template_skipped(self):
        lines = ['fetch(`/users/${id}`)', 'axios.get(`/orders/${id}`)']
        data = detect_ts_http_callers("a.ts", lines)
        self.assertEqual(data.get("callers"), [])
        self.assertTrue(len(data.get("unsupported") or []) >= 2)


if __name__ == "__main__":
    unittest.main()
