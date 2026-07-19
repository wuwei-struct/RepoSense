import unittest

from reposense.analysis.routes.typescript_decorator_classifier import (
    scan_typescript_decorators,
)
from tests.analysis._route_decorator_fixture import fixture_repo


class SwaggerParameterDecoratorNotRouteTest(unittest.TestCase):
    def test_swagger_and_parameter_decorators_are_not_routes(self):
        result = scan_typescript_decorators(fixture_repo())
        rows = result["classifications"]
        for name in ("ApiProperty", "ApiResponse", "ApiOperation"):
            self.assertTrue(
                any(
                    row["decorator_name"] == name
                    and row["classification"] == "non_route"
                    for row in rows
                )
            )
        for name in ("Body", "Param", "Query"):
            self.assertTrue(
                any(
                    row["decorator_name"] == name
                    and row["context"] == "parameter"
                    for row in rows
                )
            )


if __name__ == "__main__":
    unittest.main()
