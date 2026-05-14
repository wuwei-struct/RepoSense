def handler(request):
    # request_identity
    rid = request.get("id")
    # pre_action_guard
    if not rid:
        return "blocked"
    # time_window_only
    window = "5s"
    return "ok"
