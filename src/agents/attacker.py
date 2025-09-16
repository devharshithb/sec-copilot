from typing import Any
from .base import Agent

class Attacker(Agent):
    name = "attacker"

    def plan(self, user_goal: str) -> str:
        return "Probe external surface for open ports to hypothesize ingress."

    def act(self) -> dict[str, Any]:
        # later: request toolsmith to run nmap via policies
        return {"hypothesis": "Ports 22/80/443 likely exposed; attempt banner grab."}
