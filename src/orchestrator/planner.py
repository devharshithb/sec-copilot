def decompose(messages: list[dict]) -> str:
    """
    Very thin planner: extract the user's last message as the goal.
    Later: use LLM to produce a task tree.
    """
    for m in reversed(messages):
        if m.get("role") == "user":
            return m.get("content", "Investigate suspicious activity.")
    return "Investigate suspicious activity."
