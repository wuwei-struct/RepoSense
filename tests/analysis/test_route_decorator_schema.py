import unittest

from reposense.analysis.routes.decorator_schema import (
    normalize_classification,
)


class RouteDecoratorSchemaTest(unittest.TestCase):
    def test_stable_id_and_enums(self):
        row = {
            "file": "src/controller.ts",
            "line_start": 3,
            "decorator_name": "Get",
            "context": "method",
            "classification": "route",
            "route_method": "GET",
        }
        first = normalize_classification(row)
        second = normalize_classification(row)
        self.assertEqual(first["classification_id"], second["classification_id"])
        with self.assertRaises(ValueError):
            normalize_classification({**row, "context": "field"})
        with self.assertRaises(ValueError):
            normalize_classification({**row, "classification": "endpoint"})


if __name__ == "__main__":
    unittest.main()
