from agents import MathMentorState
def verifier_node(state: MathMentorState) -> MathMentorState:
    """STUB — Full verifier with HITL trigger implemented in Phase 2."""
    state.setdefault("agent_trace", [])
    state["agent_trace"].append({
        "agent": "Verifier",
        "action": "stub",
        "output": "Verifier not yet implemented (Phase 2)"
    })
    state["verifier_score"] = 0.0
    return state