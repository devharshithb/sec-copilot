from typing import Any
from .base import Agent

class Defender(Agent):
    name = "defender"

    def plan(self, user_goal: str) -> str:
        return "Correlate alerts; check EDR/NGFW for scans from suspicious IPs."

    def act(self) -> dict[str, Any]:
        return {"triage": "Detected SYN scan spikes from 203.0.113.12; candidate block."}
