from langgraph.graph import StateGraph, START, END
from utils.logger import get_logger
from agents import MathMentorState
from agents.parser_agent import parser_node
from agents.intent_router_agent import intent_router_node
from agents.solver_agent import solver_node
from agents.verifier_agent import verifier_node
from agents.explainer_agent import explainer_node

logger = get_logger(__name__)


def _route_from_router(state: MathMentorState) -> str:
    """
    Conditional edge after Intent Router.
    Only 'solve' continues the pipeline — everything else ends.
    """
    route = state.get("workflow_route", "error")
    logger.debug("Router conditional edge: %s", route)
    if route == "solve":
        return "solver"
    return END


def _route_from_verifier(state: MathMentorState) -> str:
    """
    Conditional edge after Verifier.
    If HITL needed → END (UI resumes pipeline after human review).
    Otherwise → explainer.
    """
    if state.get("needs_hitl", False):
        logger.info("Verifier conditional edge: HITL required — stopping pipeline")
        return END
    logger.debug("Verifier conditional edge: proceeding to explainer")
    return "explainer"


def build_graph():
    """
    Builds and compiles the full 5-agent LangGraph pipeline.
    Flow: parser → router → (solver → verifier → explainer) | END
    """
    workflow = StateGraph(MathMentorState)

    # ── Register all nodes ──────────────────────────────────────
    workflow.add_node("parser",   parser_node)
    workflow.add_node("router",   intent_router_node)
    workflow.add_node("solver",   solver_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("explainer", explainer_node)

    # ── Wire edges ──────────────────────────────────────────────
    workflow.add_edge(START, "parser")
    workflow.add_edge("parser", "router")

    # Router → solver or END (reject/hitl/clarify/error)
    workflow.add_conditional_edges(
        "router",
        _route_from_router,
        {
            "solver": "solver",
            END: END
        }
    )

    # Solver → verifier (always)
    workflow.add_edge("solver", "verifier")

    # Verifier → explainer or END (if HITL needed)
    workflow.add_conditional_edges(
        "verifier",
        _route_from_verifier,
        {
            "explainer": "explainer",
            END: END
        }
    )

    # Explainer → END
    workflow.add_edge("explainer", END)

    compiled = workflow.compile()
    logger.info("LangGraph pipeline compiled — 5 nodes: parser, router, solver, verifier, explainer")
    return compiled


# Module-level compiled graph — import this everywhere
graph = build_graph()