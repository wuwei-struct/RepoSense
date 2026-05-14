import unittest
from reposense.parsers.java_minimal import detect_java_spring_routes


class JavaRouteDetectorTest(unittest.TestCase):
    def test_get_mapping_and_prefix_join(self):
        lines = [
            "@RestController",
            '@RequestMapping("/users")',
            "class UserController {",
            '  @GetMapping("/{id}")',
            "  public String getUser(){ return \"ok\"; }",
            "}",
        ]
        rs = detect_java_spring_routes(lines)
        self.assertEqual(len(rs), 1)
        self.assertEqual(rs[0]["method"], "GET")
        self.assertEqual(rs[0]["path"], "/users/{id}")

    def test_request_mapping_method_path(self):
        lines = [
            "class Api {",
            '  @RequestMapping(method=RequestMethod.GET, path="/health")',
            "  public String health(){ return \"ok\"; }",
            "}",
        ]
        rs = detect_java_spring_routes(lines)
        self.assertEqual(len(rs), 1)
        self.assertEqual(rs[0]["method"], "GET")
        self.assertEqual(rs[0]["path"], "/health")

    def test_dynamic_path_not_reported(self):
        lines = [
            '@RequestMapping("/users")',
            "class Api {",
            '  @GetMapping(API_PREFIX + "/x")',
            "  public String x(){ return \"ok\"; }",
            "}",
        ]
        rs = detect_java_spring_routes(lines)
        self.assertEqual(rs, [])


if __name__ == "__main__":
    unittest.main()
