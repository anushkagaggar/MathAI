import os
from groq import Groq
from dotenv import load_dotenv
from utils.logger import get_logger
from agents import MathMentorState

load_dotenv()

logger = get_logger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
LLM_MODEL = os.getenv("GROQ_LLM_MODEL", "llama-3.3-70b-versatile")

EXPLAINER_SYSTEM_PROMPT = """You are a friendly, clear JEE mathematics tutor.
Rewrite the given solution as a clean, numbered step-by-step explanation for a student.

Format your response EXACTLY like this:

STEP 1: [Action taken] → [Why this works / which rule is applied]
STEP 2: [Action taken] → [Why this works / which rule is applied]
... (continue for all steps)

FINAL ANSWER: [Clearly state the final answer here]

KEY CONCEPT: [One-sentence takeaway that captures the core idea of this problem]

Rules:
- Use plain English between steps. Avoid jargon without explanation.
- Every formula you use must be named (e.g., "using the quadratic formula", "by the chain rule")
- A student who just learned this topic should fully understand each step.
- Keep it concise but complete. Do not skip any steps."""


def explainer_node(state: MathMentorState) -> MathMentorState:
    """
    LangGraph node: Produces student-friendly step-by-step explanation.
    Saves problem to memory after explanation is generated.
    """
    state.setdefault("agent_trace", [])

    solver_output = state.get("solver_output", "").strip()
    verifier_score = state.get("verifier_score", 0.0)
    needs_hitl = state.get("needs_hitl", False)

    # ── Guard: don't explain if HITL is still pending ─────────
    if needs_hitl:
        state["final_answer"] = (
            "⚠️ This solution needs human review before it can be shown. "
            "Please check the HITL panel above."
        )
        state["explanation"] = state["final_answer"]
        logger.info("Explainer: skipped — HITL pending")
        state["agent_trace"].append({
            "agent": "Explainer",
            "action": "skipped",
            "output": "HITL pending — explanation withheld"
        })
        return state

    # ── Guard: no solver output ────────────────────────────────
    if not solver_output:
        state["final_answer"] = "No solution available to explain."
        state["explanation"] = state["final_answer"]
        logger.warning("Explainer: no solver_output to explain")
        state["agent_trace"].append({
            "agent": "Explainer",
            "action": "skipped",
            "output": "No solver output"
        })
        return state

    # ── Build explainer prompt ─────────────────────────────────
    parsed = state.get("parsed_problem", {})
    problem_text = parsed.get("problem_text", state.get("extracted_text", ""))

    user_prompt = (
        f"Problem: {problem_text}\n\n"
        f"Solution to rewrite:\n{solver_output}\n\n"
        "Rewrite as a clear step-by-step explanation following the format in your instructions."
    )

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": EXPLAINER_SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt}
            ],
            max_tokens=1500,
            temperature=0.4   # Slightly creative for readable prose
        )

        explanation = response.choices[0].message.content or ""

        if not explanation.strip():
            explanation = solver_output  # Fallback to raw solver output
            logger.warning("Explainer: LLM returned empty response — using raw solver output")
        else:
            logger.info("Explainer: explanation generated (%d chars)", len(explanation))

        state["explanation"] = explanation

        # Extract final answer from explanation for quick display
        final_answer = ""
        for line in explanation.split("\n"):
            if line.strip().startswith("FINAL ANSWER:"):
                final_answer = line.replace("FINAL ANSWER:", "").strip()
                break

        state["final_answer"] = final_answer if final_answer else explanation

    except Exception as e:
        logger.error("Explainer: Groq API error: %s", str(e))
        state["explanation"] = solver_output  # Fallback
        state["final_answer"] = solver_output
        state.setdefault("agent_trace", []).append({
            "agent": "Explainer",
            "action": "error",
            "output": str(e)
        })
        return state

    # ── Save to memory ────────────────────────────────────────
    try:
        from memory.memory_store import save_problem
        problem_id = save_problem(state)
        state["last_problem_id"] = problem_id
        logger.info("Explainer: problem saved to memory with id %s", problem_id)
    except Exception as e:
        logger.warning("Explainer: failed to save to memory: %s", str(e))

    state["agent_trace"].append({
        "agent": "Explainer",
        "action": "explained",
        "output": f"Explanation generated ({len(state['explanation'])} chars) | Memory saved: {state.get('last_problem_id', 'failed')}"
    })

    return state