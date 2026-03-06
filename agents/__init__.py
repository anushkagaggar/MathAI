from typing import TypedDict, Optional


class MathMentorState(TypedDict, total=False):
    """
    Shared state that flows through all LangGraph nodes.
    All fields are optional (total=False) so nodes can update incrementally.
    IMPORTANT: Every field set by any node MUST be declared here.
    LangGraph silently drops keys not in the TypedDict.
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
    human_edited_text: str  # Text after human correction

    # ── Parser Agent Output ───────────────────────────────────────
    parsed_problem: dict    # {problem_text, topic, variables, constraints, needs_clarification}

    # ── Intent Router Output ──────────────────────────────────────
    topic: str              # "algebra"|"probability"|"calculus"|"linear_algebra"|"unknown"
    workflow_route: str     # "solve"|"hitl"|"clarify"|"reject"|"error"

    # ── Memory Context (Phase 2) ──────────────────────────────────
    memory_context: list    # Similar past problems from memory FAISS [{problem_text, answer, topic, verifier_score}]

    # ── RAG & Solver Output (Phase 2) ─────────────────────────────
    retrieved_context: list # Top-k RAG chunks: [{content, source, relevance}]
    solver_output: str      # Raw multi-step solution from Solver Agent
    sympy_result: str       # SymPy computation result string (if used)
    final_answer: str       # Polished final answer (extracted from explanation)

    # ── Verifier Output (Phase 2) ─────────────────────────────────
    verifier_score: float   # Confidence score 0.0-1.0 from Verifier Agent
    verifier_notes: str     # Verifier issues / comments

    # ── Explainer Output (Phase 2) ────────────────────────────────
    explanation: str        # STEP-by-step student-friendly explanation

    # ── Memory Persistence (Phase 2) ──────────────────────────────
    last_problem_id: str    # 8-char UUID of the saved problem in memory store

    # ── Tracing & Feedback ────────────────────────────────────────
    agent_trace: list       # [{agent: str, action: str, output: str}]
    user_feedback: str      # "correct" | "incorrect"
    user_comment: str       # User's correction comment

    # ── Error Handling ────────────────────────────────────────────
    error: str              # Error message if any step fails