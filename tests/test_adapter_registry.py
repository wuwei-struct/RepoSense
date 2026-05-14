import unittest
from reposense.adapters.registry import list_registered_languages, get_adapter, get_capability_matrix


class AdapterRegistryTest(unittest.TestCase):
    def test_registered_languages(self):
        langs = list_registered_languages()
        self.assertEqual(langs, sorted(langs))
        self.assertIn("python", langs)
        self.assertIn("sql", langs)
        self.assertIn("openapi", langs)
        self.assertIn("typescript", langs)
        self.assertIn("java", langs)

    def test_capability_matrix_stable(self):
        m = get_capability_matrix()
        self.assertIn("python", m)
        self.assertIn("sql", m)
        self.assertIn("openapi", m)
        self.assertIn("typescript", m)
        self.assertIn("java", m)
        self.assertIn("event_kinds", m["python"])
        self.assertEqual(m["python"]["event_kinds"], sorted(m["python"]["event_kinds"]))
        self.assertIn("api.route", m["typescript"]["event_kinds"])
        self.assertIn("db.transaction", m["typescript"]["event_kinds"])
        self.assertIn("queue.dispatch", m["typescript"]["event_kinds"])
        self.assertIn("queue.consume", m["typescript"]["event_kinds"])
        self.assertIn("cache.read", m["typescript"]["event_kinds"])
        self.assertIn("cache.write", m["typescript"]["event_kinds"])
        self.assertIn("cache.invalidate", m["typescript"]["event_kinds"])
        self.assertIn("api.route", m["java"]["event_kinds"])
        self.assertIn("db.transaction", m["java"]["event_kinds"])
        self.assertIn("queue.dispatch", m["java"]["event_kinds"])
        self.assertIn("queue.consume", m["java"]["event_kinds"])
        self.assertIn("db.read", m["java"]["event_kinds"])
        self.assertIn("db.write", m["java"]["event_kinds"])

    def test_get_unknown_adapter(self):
        self.assertIsNone(get_adapter("not_exists"))


if __name__ == "__main__":
    unittest.main()
