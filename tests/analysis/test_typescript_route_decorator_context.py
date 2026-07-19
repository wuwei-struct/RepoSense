import unittest

from reposense.analysis.routes.typescript_decorator_classifier import (
    classify_typescript_decorators,
    scan_typescript_decorators,
)
from tests.analysis._route_decorator_fixture import fixture_repo


class TypeScriptRouteDecoratorContextTest(unittest.TestCase):
    def test_method_property_parameter_class_and_unknown(self):
        result = scan_typescript_decorators(fixture_repo())
        rows = result["classifications"]
        self.assertTrue(
            any(
                row["decorator_name"] == "Controller"
                and row["context"] == "class"
                and row["classification"] == "controller"
                for row in rows
            )
        )
        self.assertTrue(
            any(
                row["decorator_name"] == "DeleteDateColumn"
                and row["context"] == "property"
                and row["classification"] == "non_route"
                for row in rows
            )
        )
        self.assertTrue(
            any(
                row["decorator_name"] == "Param"
                and row["context"] == "parameter"
                and row["classification"] == "non_route"
                for row in rows
            )
        )
        self.assertTrue(
            any(
                row["decorator_name"] == "Delete"
                and row["context"] == "unknown"
                and row["classification"] == "unknown"
                for row in rows
            )
        )
        self.assertFalse(
            any(
                route["file"].endswith("unknown.ts")
                for route in result["routes"]
            )
        )

    def test_route_like_module_function_after_class_is_not_a_route(self):
        result = classify_typescript_decorators(
            [
                "@Controller('items')",
                "class ItemsController {}",
                "@Delete(':id')",
                "orphan(id: string) {}",
            ],
            "src/orphan.ts",
        )
        self.assertFalse(result["routes"])
        self.assertTrue(
            any(
                row["decorator_name"] == "Delete"
                and row["classification"] == "non_route"
                for row in result["classifications"]
            )
        )


if __name__ == "__main__":
    unittest.main()
