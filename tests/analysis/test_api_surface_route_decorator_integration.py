import json
import os
import shutil
import unittest

from reposense.ci import run_ci
from tests._tmpdir import make_temp_dir
from tests.analysis._route_decorator_fixture import fixture_repo


class ApiSurfaceRouteDecoratorIntegrationTest(unittest.TestCase):
    def test_api_surface_uses_canonical_routes(self):
        out_dir = make_temp_dir(prefix="route_decorator_ci_")
        try:
            code = run_ci(
                fixture_repo(),
                out_dir,
                profile="demo",
                with_context_pack=False,
                json_stdout=False,
            )
            self.assertIn(code, (0, 2))
            run_dir = sorted(
                os.path.join(out_dir, name)
                for name in os.listdir(out_dir)
                if name.startswith("run-")
            )[-1]
            with open(
                os.path.join(run_dir, "api_surface.json"),
                "r",
                encoding="utf-8",
            ) as handle:
                endpoints = json.load(handle)["endpoints"]
            keys = {
                (row["method"], row["path"])
                for row in endpoints
                if row.get("framework") == "nestjs"
            }
            self.assertIn(("DELETE", "/api/{id}"), keys)
            self.assertIn(("PATCH", "/api/orders/{id}"), keys)
            self.assertFalse(
                any(
                    "order.entity.ts" in str(row.get("source") or "")
                    for row in endpoints
                )
            )
            self.assertTrue(
                os.path.isfile(
                    os.path.join(
                        run_dir,
                        "route_decorator_classifications.json",
                    )
                )
            )
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
