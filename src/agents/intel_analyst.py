from typing import Any
from .base import Agent

class IntelAnalyst(Agent):
    name = "intel_analyst"

    def plan(self, user_goal: str) -> str:
        return "Query CTI + Reddit/SO for recent scanning campaigns & IOCs."

    def act(self) -> dict[str, Any]:
        # later: call reddit/stackoverflow clients; now stub
        return {"intel": ["Recent mass-scan campaigns on 22/443 reported this week."]}
