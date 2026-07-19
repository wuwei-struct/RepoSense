import json
import os
import shutil
import unittest

from reposense.analysis.authz.authz_scanner import scan_permission_auditor
from tests._tmpdir import make_temp_dir


class OpenAPISecurityNotImplementationProofTest(unittest.TestCase):
    def test_openapi_security_does_not_suppress_missing_auth(self):
        repo = make_temp_dir(prefix="openapi_not_proof_repo_")
        run_dir = make_temp_dir(prefix="openapi_not_proof_run_")
        try:
            os.makedirs(os.path.join(repo, "src"), exist_ok=True)
            with open(
                os.path.join(repo, "src", "orders.controller.ts"),
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write(
                    "@Controller('orders')\n"
                    "export class OrdersController {\n"
                    "  @Post()\n"
                    "  createOrder() { return {}; }\n"
                    "}\n"
                )
            with open(
                os.path.join(repo, "openapi.yaml"),
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write(
                    "openapi: 3.0.3\n"
                    "info: {title: Test, version: 1.0.0}\n"
                    "security:\n"
                    "  - bearerAuth: []\n"
                    "paths:\n"
                    "  /orders:\n"
                    "    post:\n"
                    "      responses: {'200': {description: ok}}\n"
                )
            with open(
                os.path.join(run_dir, "api_surface.json"),
                "w",
                encoding="utf-8",
            ) as handle:
                json.dump(
                    {
                        "endpoints": [
                            {
                                "method": "POST",
                                "normalized_path": "/orders",
                                "path": "/orders",
                                "source_kind": "openapi",
                                "source": {
                                    "path": "src/orders.controller.ts",
                                    "line_start": 3,
                                },
                            }
                        ]
                    },
                    handle,
                )
            _surface, risks = scan_permission_auditor(run_dir, repo)
            missing_auth = [
                row
                for row in risks["risks"]
                if row["rule_id"] in {"AUTHZ-001", "AUTHZ-002"}
            ]
            self.assertTrue(missing_auth)
            self.assertTrue(
                any(
                    "openapi_security_without_code_guard"
                    in row.get("limitations", [])
                    for row in missing_auth
                )
            )
        finally:
            shutil.rmtree(repo, ignore_errors=True)
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
