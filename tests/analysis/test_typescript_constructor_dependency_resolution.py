import unittest

from reposense.analysis.typescript.import_graph import build_typescript_index
from tests.analysis.test_typescript_import_graph_schema import FIXTURE


class TypeScriptConstructorDependencyResolutionTest(unittest.TestCase):
    def test_multiline_and_alias_constructor_types_are_indexed(self):
        index = build_typescript_index(FIXTURE)
        services = index["files"]["src/services.ts"]
        alias = services["constructor_dependencies"]["AliasService"][0]
        dynamic = index["files"]["src/ambiguous.ts"][
            "constructor_dependencies"
        ]["DynamicService"][0]
        self.assertEqual(alias["name"], "accounts")
        self.assertEqual(alias["declared_type"], "AccountRepository")
        self.assertEqual(
            dynamic["dynamic_inject_token"], "'DYNAMIC_REPOSITORY'"
        )


if __name__ == "__main__":
    unittest.main()
