import os


RULES = {
    "AUTHZ-001": "Public write endpoint",
    "AUTHZ-002": "Route missing auth guard",
    "AUTHZ-003": "Sensitive route missing role guard",
    "AUTHZ-004": "Frontend-only permission check",
    "AUTHZ-005": "Permission negative test gap",
}

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SENSITIVE_WORDS = {
    "admin",
    "user",
    "account",
    "billing",
    "payment",
    "order",
    "refund",
    "delete",
    "settings",
    "workspace",
    "organization",
    "tenant",
    "role",
    "permission",
}
AUTH_WORDS = [
    "requireAuth",
    "authRequired",
    "authenticate",
    "isAuthenticated",
    "PreAuthorize",
    "RolesAllowed",
    "Secured",
    "UseGuards",
    "AuthGuard",
    "JwtAuthGuard",
    "RolesGuard",
    "passport",
    "jwt",
    "session",
    "canActivate",
    "login_required",
    "permission_required",
    "user.is_authenticated",
    "authorize",
    "requirePermission",
    "requireRole",
]
ROLE_WORDS = [
    "requireRole",
    "requirePermission",
    "hasRole",
    "hasAuthority",
    "@Roles",
    "PreAuthorize",
    "permission:",
    "permissions:",
    ".can(",
    "policy",
    "ability",
    "RBAC",
    "ACL",
    "isAdmin",
    "adminOnly",
]
FRONTEND_WORDS = [
    "isAdmin",
    "hasPermission",
    "canAccess",
    "role ===",
    "permissions.includes",
    "<Can",
    "v-if",
    "disabled",
]
NEGATIVE_TEST_WORDS = [
    "401",
    "403",
    "unauthorized",
    "forbidden",
    "non-admin",
    "anonymous",
    "unauthenticated",
    "permission denied",
    "should reject",
    "cannot access",
    "tenant mismatch",
    "different user",
    "owner mismatch",
]
SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java"}
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", "dist", "build", ".tmp_test_runs", ".reposense_ci", ".reposense_demo", ".reposense_release_demo"}


def is_test_path(path):
    p = path.replace("\\", "/").lower()
    base = os.path.basename(p)
    return "/test/" in p or "/tests/" in p or base.startswith("test_") or ".test." in base or ".spec." in base or base.endswith(("test.java", "tests.java"))


def is_frontend_path(path):
    p = path.replace("\\", "/").lower()
    return any(x in p for x in ["frontend", "client", "web", "ui", "components"]) or p.endswith((".tsx", ".jsx"))


def language_for_path(path):
    ext = os.path.splitext(path.lower())[1]
    return {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
    }.get(ext, "unknown")

