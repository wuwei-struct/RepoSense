def get_ai_insight_boundary_stub():
    return {
        "included_in_oss": False,
        "message": (
            "AI Insight is not included in the open-source engine. "
            "Use local evidence-backed reports in OSS; hosted/commercial layers may provide "
            "guided explanation enhancement, repair suggestions, team history, and enterprise reporting."
        ),
    }


def render_ai_insight_boundary():
    obj = get_ai_insight_boundary_stub()
    return (
        "included_in_oss={inc}\nmessage={msg}".format(
            inc=str(obj.get("included_in_oss")),
            msg=str(obj.get("message") or ""),
        )
    )

