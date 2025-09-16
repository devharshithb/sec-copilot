from typing import Any
from .base import Agent

class Decider(Agent):
    name = "decider"

    def plan(self, user_goal: str) -> str:
        return "Evaluate risk & cost-benefit; approve or deny containment."

    def act(self) -> dict[str, Any]:
        # later: use policy thresholds, risk scoring
        return {"decision": "Block IP at edge firewall; schedule service validation post-block."}
