from pydantic import BaseModel, Field
from typing import Any, Literal

Role = Literal["attacker", "defender", "decider", "intel_analyst", "toolsmith"]

class ToolCall(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)

class TraceStep(BaseModel):
    step_id: str
    agent: Role
    rationale: str
    tool_calls: list[ToolCall] = []
    evidence: list[str] = []     # URLs, hashes, log refs
    outputs: dict[str, Any] = {} # structured results
    confidence: float = 0.5
    policy_hits: list[str] = []  # which policy checks triggered

class FinalDecision(BaseModel):
    summary: str
    risk_score: float            # 0 (no risk) -> 1 (high risk)
    recommendations: list[str]

class ConversationResult(BaseModel):
    steps: list[TraceStep]
    final: FinalDecision
