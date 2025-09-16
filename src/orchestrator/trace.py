import uuid
from src.utils.schema import TraceStep, ToolCall

def make_step(agent: str, rationale: str, outputs: dict, tool_calls: list[dict]|None=None, policy_hits: list[str]|None=None, confidence: float=0.6) -> TraceStep:
    return TraceStep(
        step_id=str(uuid.uuid4()),
        agent=agent, rationale=rationale,
        outputs=outputs,
        tool_calls=[ToolCall(**t) for t in (tool_calls or [])],
        policy_hits=policy_hits or [],
        confidence=confidence,
    )
