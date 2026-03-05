from langgraph.graph import StateGraph, START, END
from agents import MathMentorState
from agents.parser_agent import parser_node
from agents.intent_router_agent import intent_router_node
from agents.solver_agent import solver_node
from agents.verifier_agent import verifier_node
from agents.explainer_agent import explainer_node


def _route_from_router(state: MathMentorState) -> str:
    """Conditional edge: routes based on workflow_route set by intent_router_node."""
    route = state.get("workflow_route", "error")
    # Map all terminal routes to END, only "solve" continues pipeline
    if route == "solve":
        return "solver"
    return END


def build_graph():
    """
    Builds and compiles the full LangGraph agent pipeline.
    Phase 1: parser → router → (solver stub or END)
    Phase 2: solver → verifier → explainer will be wired in
    """
    workflow = StateGraph(MathMentorState)

    # ── Register nodes ────────────────────────────────────────────
    workflow.add_node("parser", parser_node)
    workflow.add_node("router", intent_router_node)
    workflow.add_node("solver", solver_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("explainer", explainer_node)

    # ── Wire edges ────────────────────────────────────────────────
    workflow.add_edge(START, "parser")
    workflow.add_edge("parser", "router")

    # Conditional edge from router
    workflow.add_conditional_edges(
        "router",
        _route_from_router,
        {
            "solver": "solver",
            END: END
        }
    )

    # Phase 2 chain (stubs for now, will have logic in Phase 2)
    workflow.add_edge("solver", "verifier")
    workflow.add_edge("verifier", "explainer")
    workflow.add_edge("explainer", END)

    return workflow.compile()


# Module-level compiled graph — import this everywhere
graph = build_graph()