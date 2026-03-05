from agents import MathMentorState
def explainer_node(state: MathMentorState) -> MathMentorState:
    """STUB — Full step-by-step explainer implemented in Phase 2."""
    state.setdefault("agent_trace", [])
    state["agent_trace"].append({
        "agent": "Explainer",
        "action": "stub",
        "output": "Explainer not yet implemented (Phase 2)"
    })
    return state