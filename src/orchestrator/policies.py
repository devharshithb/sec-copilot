# simple policy primitives; later read YAML from policies/tool_allowlist.yaml
ALLOWED_TOOLS = {"nmap": {"allowed_flags": ["-sS", "-sV", "-Pn", "-T4"]}}

def validate_tool_request(name: str, args: dict) -> list[str]:
    hits = []
    if name not in ALLOWED_TOOLS:
        hits.append("tool_not_allowed")
        return hits
    # simple arg check (expand later)
    flags = args.get("scan", "")
    for token in flags.split():
        if token.startswith("-") and token not in ALLOWED_TOOLS[name]["allowed_flags"]:
            hits.append(f"flag_not_allowed:{token}")
    return hits
