import unittest

from reposense.analysis.context.context_schema import ROUTE_INTENTS, normalize_route_intent


class RouteIntentSchemaTest(unittest.TestCase):
    def test_stable_id_and_allowed_intent(self):
        item = {
            "method": "POST",
            "path": "/auth/login",
            "file": "src/auth.ts",
            "line_start": 3,
            "intent": "public_auth_entrypoint",
            "signals": ["public_auth:login"],
        }
        first = normalize_route_intent(item)
        second = normalize_route_intent(item)
        self.assertEqual(first["annotation_id"], second["annotation_id"])
        self.assertIn(first["intent"], ROUTE_INTENTS)
        self.assertFalse(first["file"].startswith(("C:", "/tmp/")))


if __name__ == "__main__":
    unittest.main()
