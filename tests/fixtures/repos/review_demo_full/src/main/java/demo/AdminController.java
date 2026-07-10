package demo;

public class AdminController {
    @PostMapping("/admin/rebuild")
    @RequireAuth
    public String rebuild() {
        // FIXME: role guard is intentionally absent for Permission Auditor demo.
        return "scheduled";
    }
}

@interface RequireAuth {}

