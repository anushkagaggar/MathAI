from agents import MathMentorState
from utils.logger import get_logger
logger = get_logger(__name__)

def intent_router_node(state: MathMentorState) -> MathMentorState:
    """
    LangGraph node: Classifies intent, sets workflow_route.
    Pure Python logic — no LLM call (keeps it fast and deterministic).

    Routes:
        "error"   → error state set upstream
        "hitl"    → HITL triggered (low confidence or ambiguity)
        "reject"  → not a math problem in scope
        "clarify" → parser flagged needs_clarification
        "solve"   → proceed to Solver Agent
    """
    state.setdefault("agent_trace", [])

    # ── Route 1: Error from upstream ─────────────────────────────
    if state.get("error"):
        state["workflow_route"] = "error"
        state["agent_trace"].append({
            "agent": "Intent Router",
            "action": "routed",
            "output": "Route: error — upstream error detected"
        })
        return state

    # ── Route 2: HITL triggered (low confidence or ambiguity) ─────
    if state.get("needs_hitl", False):
        state["workflow_route"] = "hitl"
        state["agent_trace"].append({
            "agent": "Intent Router",
            "action": "routed",
            "output": f"Route: hitl — reason: {state.get('hitl_reason', 'unspecified')}"
        })
        return state

    parsed = state.get("parsed_problem", {})

    # ── Route 3: Unknown topic → reject ──────────────────────────
    if not parsed or parsed.get("topic", "unknown") == "unknown":
        state["workflow_route"] = "reject"
        state["agent_trace"].append({
            "agent": "Intent Router",
            "action": "routed",
            "output": "Route: reject — topic is unknown or not in scope"
        })
        return state

    # ── Route 4: Parser flagged clarification needed ──────────────
    if parsed.get("needs_clarification", False):
        state["workflow_route"] = "clarify"
        state["agent_trace"].append({
            "agent": "Intent Router",
            "action": "routed",
            "output": f"Route: clarify — {parsed.get('clarification_reason', 'ambiguous problem')}"
        })
        return state

    # ── Route 5: All clear → solve ────────────────────────────────
    topic = parsed.get("topic", "unknown")
    state["workflow_route"] = "solve"
    state["agent_trace"].append({
        "agent": "Intent Router",
        "action": "routed",
        "output": f"Route: solve — topic: {topic}"
    })

    return state