from typing import TypedDict, Optional


class MathMentorState(TypedDict, total=False):
    """
    Shared state that flows through all LangGraph nodes.
    All fields are optional (total=False) so nodes can update incrementally.
    """
    # ── Input Processing ──────────────────────────────────────────
    raw_input: str          # Original input before any processing
    input_type: str         # "text" | "image" | "audio"
    extracted_text: str     # Text after OCR/ASR/passthrough
    confidence: float       # Input processor confidence score (0.0-1.0)

    # ── HITL Flags ────────────────────────────────────────────────
    needs_hitl: bool        # True = pause for human review
    hitl_reason: str        # Why HITL was triggered
    hitl_approved: bool     # True = human approved and we can proceed
    human_edited_text: str  # Text after human correction (Phase 2/3)

    # ── Parser Agent Output ───────────────────────────────────────
    parsed_problem: dict    # Structured problem: {problem_text, topic, variables, constraints, needs_clarification, clarification_reason}

    # ── Intent Router Output ──────────────────────────────────────
    topic: str              # "algebra"|"probability"|"calculus"|"linear_algebra"|"unknown"
    workflow_route: str     # "solve"|"hitl"|"clarify"|"reject"|"error"

    # ── RAG & Solver Output (Phase 2) ─────────────────────────────
    retrieved_context: list # Top-k chunks from RAG: [{content, source, relevance}]
    solver_output: str      # Raw solution from Solver Agent
    sympy_result: str       # SymPy computation result if used
    final_answer: str       # Polished final answer

    # ── Verifier Output (Phase 2) ─────────────────────────────────
    verifier_score: float   # Confidence score from Verifier Agent
    verifier_notes: str     # Verifier comments on correctness

    # ── Explainer Output (Phase 2) ────────────────────────────────
    explanation: str        # Step-by-step student-friendly explanation

    # ── Tracing & Feedback ────────────────────────────────────────
    agent_trace: list       # [{agent: str, action: str, output: str}]
    user_feedback: str      # "correct" | "incorrect"
    user_comment: str       # User's correction comment

    # ── Error Handling ────────────────────────────────────────────
    error: str              # Error message if any step fails