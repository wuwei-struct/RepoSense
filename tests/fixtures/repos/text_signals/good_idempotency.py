def handler(request):
    # request_identity
    rid = request.get("id")
    # pre_action_guard
    if not rid:
        return "blocked"
    # unique_constraint
    unique = True
    # result_cache
    cache_key = f"result_cache:{rid}"
    return "ok"
