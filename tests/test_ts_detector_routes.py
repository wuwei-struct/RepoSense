import unittest
from reposense.parsers.typescript_minimal import detect_ts_express_routes, detect_ts_nest_routes


class TsDetectorRoutesTest(unittest.TestCase):
    def test_express_routes_literal(self):
        lines = [
            'app.get("/health", handler)',
            'router.post("/orders", handler)',
            'app[method]("/x", handler)',
        ]
        hits = detect_ts_express_routes(lines)
        keys = sorted([(h["method"], h["path"]) for h in hits])
        self.assertIn(("GET", "/health"), keys)
        self.assertIn(("POST", "/orders"), keys)
        self.assertNotIn(("GET", "/x"), keys)

    def test_nest_routes(self):
        lines = [
            '@Controller("users")',
            "class UsersController {",
            "  @Get()",
            "  list() {}",
            '  @Post(":id")',
            "  create() {}",
            "}",
        ]
        hits = detect_ts_nest_routes(lines)
        keys = sorted([(h["method"], h["path"]) for h in hits])
        self.assertIn(("GET", "/users"), keys)
        self.assertIn(("POST", "/users/{id}"), [(m, p.replace(":id", "{id}")) for m, p in keys])


if __name__ == "__main__":
    unittest.main()
