from abc import ABC, abstractmethod
from typing import Any

class Agent(ABC):
    name: str

    def __init__(self, blackboard: "Blackboard"):
        self.blackboard = blackboard

    @abstractmethod
    def plan(self, user_goal: str) -> str:
        ...

    @abstractmethod
    def act(self) -> dict[str, Any]:
        ...

    def observe(self, data: dict[str, Any]) -> None:
        # default: store in blackboard
        self.blackboard.append_observation(self.name, data)

    def report(self) -> str:
        return f"{self.name} completed action."
