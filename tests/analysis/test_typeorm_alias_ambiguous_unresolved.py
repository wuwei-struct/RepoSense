import unittest

from reposense.analysis.typescript.import_graph import build_typescript_index
from reposense.analysis.typescript.wrapper_resolution import (
    resolve_typeorm_wrappers,
)
from tests.analysis.test_typeorm_wrapper_method_resolution import (
    FIXTURE,
    fake_operations,
)


class TypeOrmAliasAmbiguousUnresolvedTest(unittest.TestCase):
    def test_dynamic_di_is_not_guessed(self):
        rows, _ = resolve_typeorm_wrappers(
            build_typescript_index(FIXTURE), fake_operations()
        )
        dynamic = [
            item for item in rows if item["source_class"] == "DynamicService"
        ]
        self.assertFalse(
            any(
                item["resolution_status"].startswith("resolved_")
                for item in dynamic
            )
        )


if __name__ == "__main__":
    unittest.main()
