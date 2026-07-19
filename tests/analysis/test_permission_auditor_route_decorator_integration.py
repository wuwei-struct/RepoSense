import json
import os
import shutil
import unittest

from reposense.analysis.authz.authz_matrix_infer import infer_authz_matrix
from tests.analysis._route_decorator_fixture import build_decorator_run


class PermissionAuditorRouteDecoratorIntegrationTest(unittest.TestCase):
    def test_non_routes_do_not_reappear_downstream(self):
        run_dir, result = build_decorator_run()
        try:
            routes = result["surface"]["routes"]
            risks = result["risks"]["risks"]
            self.assertFalse(
                any(
                    row["file"].endswith("order.entity.ts")
                    for row in routes
                )
            )
            self.assertFalse(
                any(
                    str(row.get("file") or "").endswith("order.entity.ts")
                    for row in risks
                )
            )
            inferred = infer_authz_matrix(result["surface"], result["risks"])
            encoded = json.dumps(inferred, ensure_ascii=False)
            self.assertNotIn("DeleteDateColumn", encoded)
            self.assertNotIn("order.entity.ts", encoded)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
