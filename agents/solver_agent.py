from agents import MathMentorState
def solver_node(state: MathMentorState) -> MathMentorState:
    """STUB — Full RAG + SymPy solver implemented in Phase 2."""
    state.setdefault("agent_trace", [])
    state["agent_trace"].append({
        "agent": "Solver",
        "action": "stub",
        "output": "Solver not yet implemented (Phase 2)"
    })
    state["solver_output"] = "[Phase 2] Solver stub — not yet implemented"
    return state
