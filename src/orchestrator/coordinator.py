from typing import Literal
from src.utils.schema import ConversationResult, FinalDecision
from src.orchestrator.blackboard import Blackboard
from src.orchestrator.trace import make_step
from src.orchestrator.policies import validate_tool_request
from src.agents.attacker import Attacker
from src.agents.defender import Defender
from src.agents.decider import Decider
from src.agents.intel_analyst import IntelAnalyst
from src.agents.toolsmith import Toolsmith
from src.utils.schema import TraceStep

def run_conversation(messages: list[dict], mode: Literal["assist","simulate"]="assist", game_id: str|None=None) -> dict:
    """
    Turn engine v0: one pass of (intel -> attacker -> defender -> toolsmith -> decider).
    Emits traceable steps you can show in the UI.
    """
    bb = Blackboard()
    steps: list[TraceStep] = []

    goal = __import__("src.orchestrator.planner", fromlist=["decompose"]).decompose(messages)

    # instantiate agents
    attacker = Attacker(bb)
    defender = Defender(bb)
    decider  = Decider(bb)
    intel    = IntelAnalyst(bb)
    tools    = Toolsmith(bb)

    # Intel phase
    rationale = intel.plan(goal)
    outputs = intel.act()
    intel.observe(outputs)
    steps.append(make_step("intel_analyst", rationale, outputs))

    # Attacker hypothesis
    rationale = attacker.plan(goal)
    outputs = attacker.act()
    attacker.observe(outputs)
    steps.append(make_step("attacker", rationale, outputs))

    # Defender triage
    rationale = defender.plan(goal)
    outputs = defender.act()
    defender.observe(outputs)
    steps.append(make_step("defender", rationale, outputs))

    # Toolsmith proposes tools -> policy check (no execution yet)
    rationale = tools.plan(goal)
    tool_outputs = tools.act()
    hits: list[str] = []
    for t in tool_outputs.get("tools_requested", []):
        hits.extend(validate_tool_request(t["name"], t.get("args", {})))
    steps.append(make_step("toolsmith", rationale, tool_outputs, tool_calls=tool_outputs.get("tools_requested", []), policy_hits=hits))

    # Decider makes a recommendation (later: consider bb, hits, intel credibility)
    rationale = decider.plan(goal)
    outputs = decider.act()
    decider.observe(outputs)
    steps.append(make_step("decider", rationale, outputs, policy_hits=hits))

    final = FinalDecision(
        summary=outputs.get("decision", "No decision."),
        risk_score=0.6 if not hits else 0.4,  # toy logic
        recommendations=[outputs.get("decision", "Document findings.")]
    )

    return ConversationResult(steps=steps, final=final).model_dump()
