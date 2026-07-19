import unittest

from reposense.analysis.routes.typescript_decorator_classifier import (
    classify_typescript_decorators,
)


class TypeScriptRouteDecoratorExactMatchTest(unittest.TestCase):
    def test_exact_symbols_only(self):
        lines = [
            "@Controller('items')",
            "class ItemsController {",
            "  @Delete(':id')",
            "  remove() {}",
            "  @DeleteDateColumn()",
            "  deletedAt: Date;",
            "  @GetUser()",
            "  helper() {}",
            "  @PostConstruct()",
            "  initialize() {}",
            "}",
        ]
        result = classify_typescript_decorators(lines, "src/items.ts")
        self.assertEqual(
            [(row["method"], row["path"]) for row in result["routes"]],
            [("DELETE", "/items/{id}")],
        )
        rejected = {
            row["decorator_name"]: row["classification"]
            for row in result["classifications"]
        }
        self.assertEqual(rejected["DeleteDateColumn"], "non_route")
        self.assertEqual(rejected["GetUser"], "non_route")
        self.assertEqual(rejected["PostConstruct"], "non_route")


if __name__ == "__main__":
    unittest.main()
