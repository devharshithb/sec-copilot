from typing import Any

class Blackboard:
    def __init__(self):
        self.store: dict[str, list[dict[str, Any]]] = {}

    def append_observation(self, agent: str, data: dict[str, Any]):
        self.store.setdefault(agent, []).append(data)

    def get_all(self) -> dict[str, list[dict[str, Any]]]:
        return self.store
