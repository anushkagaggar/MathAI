import os
import json
from groq import Groq
from utils.groq_client import get_groq_client
from dotenv import load_dotenv
from utils.logger import get_logger
from agents import MathMentorState

load_dotenv()

logger = get_logger(__name__)

LLM_MODEL = os.getenv("GROQ_LLM_MODEL", "llama-3.3-70b-versatile")

VERIFIER_SYSTEM_PROMPT = """You are a strict mathematical verifier for JEE-level problems.
Your job is to critically review a proposed solution and assign a confidence score.

Respond ONLY with a valid JSON object — no markdown, no extra text:
{
  "score": <float 0.0-1.0>,
  "verdict": "<correct|incorrect|uncertain>",
  "issues": ["<issue 1>", "<issue 2>"],
  "domain_valid": <true|false>,
  "matches_sympy": <true|false|null>
}

Scoring guide:
- 0.9-1.0: Completely correct, all steps valid, final answer verified
- 0.7-0.89: Likely correct but minor gaps or unclear steps
- 0.5-0.69: Uncertain — some steps questionable or answer unverified
- 0.0-0.49: Incorrect — wrong answer, invalid steps, or domain violation

Domain checks:
- Probability answers must be in [0, 1]
- No division by zero
- Square roots of negatives flagged (unless complex numbers are in scope)
- Matrix dimensions must be compatible for operations"""


def _check_domain_violations(solver_output: str, topic: str) -> list:
    """Fast heuristic checks before sending to LLM."""
    violations = []

    if topic == "probability":
        import re
        numbers = re.findall(r'(?:=|is|answer|probability[:\s]+)\s*([0-9]+(?:\.[0-9]+)?)', solver_output.lower())
        for num_str in numbers:
            try:
                val = float(num_str)
                if val > 1.0:
                    violations.append(f"Probability value {val} exceeds 1.0 — invalid")
            except ValueError:
                pass

    if "divide by 0" in solver_output.lower() or "division by zero" in solver_output.lower():
        violations.append("Possible division by zero detected")

    return violations


def verifier_node(state: MathMentorState) -> MathMentorState:
    """
    LangGraph node: Reviews solver output for correctness.
    Sets verifier_score, verifier_notes.
    Triggers HITL if score < threshold or verdict is 'incorrect'.
    """
    state.setdefault("agent_trace", [])

    solver_output = state.get("solver_output", "").strip()
    topic = state.get("topic", "unknown")
    sympy_result = state.get("sympy_result", "")
    parsed = state.get("parsed_problem", {})

    verifier_threshold = float(os.getenv("VERIFIER_CONFIDENCE_THRESHOLD", "0.80"))

    # ── Guard: empty or error output ────────────────────────────
    if not solver_output or "solver error" in solver_output.lower():
        state["verifier_score"] = 0.0
        state["verifier_notes"] = "Solver produced no output or errored — cannot verify"
        state["needs_hitl"] = True
        state["hitl_reason"] = "Solver produced no output. Please re-check the problem."
        logger.warning("Verifier: empty/error solver output — immediate HITL")
        state["agent_trace"].append({
            "agent": "Verifier",
            "action": "failed",
            "output": "Empty solver output — HITL triggered"
        })
        return state

    # ── Fast domain checks ───────────────────────────────────────
    domain_violations = _check_domain_violations(solver_output, topic)
    if domain_violations:
        logger.warning("Verifier: domain violations found: %s", domain_violations)

    # ── SymPy cross-check ────────────────────────────────────────
    sympy_mismatch = False
    if sympy_result and sympy_result not in ("Not available", ""):
        # Check if SymPy's numbers appear somewhere in the solver output
        import re
        sympy_nums = re.findall(r'-?\d+(?:\.\d+)?', sympy_result)
        solver_nums = re.findall(r'-?\d+(?:\.\d+)?', solver_output)
        if sympy_nums:
            match_count = sum(1 for n in sympy_nums if n in solver_nums)
            if match_count < len(sympy_nums) * 0.5:
                sympy_mismatch = True
                logger.warning("Verifier: SymPy result %s may not match solver output", sympy_result[:60])

    # ── Build verifier prompt ────────────────────────────────────
    problem_text = parsed.get("problem_text", state.get("extracted_text", ""))

    user_prompt_lines = [
        f"Problem: {problem_text}",
        f"Topic: {topic}",
        "",
        "Proposed Solution:",
        solver_output[:1500],  # Trim to avoid token overflow
        ""
    ]

    if sympy_result and sympy_result not in ("Not available", ""):
        user_prompt_lines.append(f"SymPy Ground Truth: {sympy_result}")
        user_prompt_lines.append("Check if the proposed solution's final answer matches this.")
        user_prompt_lines.append("")

    if domain_violations:
        user_prompt_lines.append(f"Pre-detected domain violations: {domain_violations}")
        user_prompt_lines.append("")

    user_prompt_lines.append("Verify the solution and respond with JSON only.")
    user_prompt = "\n".join(user_prompt_lines)

    # ── Call Groq LLM ─────────────────────────────────────────────
    try:
        response = get_groq_client().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": VERIFIER_SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt}
            ],
            max_tokens=600,
            temperature=0.1   # Conservative for verification
        )

        raw = response.choices[0].message.content or ""

        # Strip markdown fences
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        clean = clean.strip()

        verdict_data = json.loads(clean)

        score = float(verdict_data.get("score", 0.6))
        verdict = verdict_data.get("verdict", "uncertain")
        issues = verdict_data.get("issues", [])

        # Penalise if we detected SymPy mismatch
        if sympy_mismatch:
            score = min(score, 0.65)
            issues.append(f"SymPy computed {sympy_result} but solver answer may differ")

        # Penalise domain violations
        if domain_violations:
            score = min(score, 0.5)
            issues.extend(domain_violations)

        state["verifier_score"] = round(score, 3)
        state["verifier_notes"] = "; ".join(issues) if issues else "No issues found"
        logger.info("Verifier: score=%.2f, verdict=%s, issues=%d", score, verdict, len(issues))

    except json.JSONDecodeError as e:
        # Graceful fallback
        score = 0.6
        verdict = "uncertain"
        state["verifier_score"] = score
        state["verifier_notes"] = f"Verifier could not parse response (fallback score). Raw: {raw[:100]}"
        logger.warning("Verifier: JSON parse failed — using fallback score 0.6: %s", str(e))

    except Exception as e:
        score = 0.6
        verdict = "uncertain"
        state["verifier_score"] = score
        state["verifier_notes"] = f"Verifier API error: {str(e)}"
        logger.error("Verifier: Groq API error: %s", str(e))

    # ── HITL decision ─────────────────────────────────────────────
    needs_hitl = False
    hitl_reason = ""

    if score < verifier_threshold:
        needs_hitl = True
        hitl_reason = (
            f"Verifier confidence too low ({score:.0%}). "
            f"Issues: {state['verifier_notes']}"
        )
        logger.warning("Verifier: HITL triggered — score %.2f below threshold %.2f", score, verifier_threshold)

    elif verdict == "incorrect":
        needs_hitl = True
        hitl_reason = f"Verifier found incorrect solution. Issues: {state['verifier_notes']}"
        logger.warning("Verifier: HITL triggered — verdict=incorrect")

    if needs_hitl:
        state["needs_hitl"] = True
        state["hitl_reason"] = hitl_reason

    state["agent_trace"].append({
        "agent": "Verifier",
        "action": "verified",
        "output": (
            f"Score: {state['verifier_score']:.2f} | "
            f"Verdict: {verdict} | "
            f"HITL: {'yes — ' + hitl_reason[:60] if needs_hitl else 'no'}"
        )
    })

    return state