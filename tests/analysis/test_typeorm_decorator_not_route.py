import unittest

from reposense.analysis.routes.typescript_decorator_classifier import (
    scan_typescript_decorators,
)
from tests.analysis._route_decorator_fixture import fixture_repo


class TypeOrmDecoratorNotRouteTest(unittest.TestCase):
    def test_typeorm_property_decorators_are_rejected(self):
        result = scan_typescript_decorators(fixture_repo())
        names = {
            row["decorator_name"]
            for row in result["classifications"]
            if row["classification"] == "non_route"
        }
        for name in (
            "DeleteDateColumn",
            "CreateDateColumn",
            "UpdateDateColumn",
            "Column",
            "PrimaryGeneratedColumn",
        ):
            self.assertIn(name, names)
        self.assertFalse(
            any(
                route["file"].endswith("order.entity.ts")
                for route in result["routes"]
            )
        )


if __name__ == "__main__":
    unittest.main()
