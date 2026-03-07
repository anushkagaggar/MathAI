import os
import json
from groq import Groq
from utils.groq_client import get_groq_client
from dotenv import load_dotenv
from agents import MathMentorState
from utils.logger import get_logger

logger = get_logger(__name__)

load_dotenv()

import re as _re

def _safe_json_loads(text: str) -> dict:
    """
    Robustly parse JSON that may contain LaTeX backslashes.
    json.loads rejects bare \\int, \\frac etc — this pre-sanitizes them.
    """
    s = text.strip()
    # Strip markdown fences
    if s.startswith("```"):
        s = s.split("```")[1]
        if s.startswith("json"):
            s = s[4:]
    s = s.strip()
    # Extract outermost { ... }
    b1, b2 = s.find("{"), s.rfind("}")
    if b1 != -1 and b2 != -1:
        s = s[b1:b2+1]
    # Fix lone backslashes that are not valid JSON escape sequences
    # Valid: \\ \" \/ \b \f \n \r \t \uXXXX
    s = _re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', s)
    return __import__("json").loads(s)

LLM_MODEL = os.getenv("GROQ_LLM_MODEL", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = """You are a math problem parser for JEE-level problems.
Given a math problem text, extract its structure and return ONLY a valid JSON object.
No markdown fences, no explanation, no extra text — ONLY the JSON.

Schema:
{
  "problem_text": "cleaned, complete problem statement",
  "topic": "one of: algebra | probability | calculus | linear_algebra | unknown",
  "variables": ["list", "of", "variables", "used"],
  "constraints": ["list of constraints or given conditions"],
  "needs_clarification": false,
  "clarification_reason": ""
}

Rules:
- topic must be exactly one of the five options listed
- needs_clarification = true only if the problem is genuinely ambiguous or incomplete
- If it is not a math problem at all, set topic = "unknown" and needs_clarification = true
- variables should include all symbolic unknowns (x, y, θ, etc.)
- constraints include things like "x > 0", "n is a positive integer", given values"""


def parser_node(state: MathMentorState) -> MathMentorState:
    """
    LangGraph node: Parses extracted_text into structured problem dict.
    Updates: parsed_problem, needs_hitl, hitl_reason, agent_trace
    """
    state.setdefault("agent_trace", [])
    state.setdefault("needs_hitl", False)
    state.setdefault("hitl_reason", "")

    extracted_text = state.get("extracted_text", "").strip()

    if not extracted_text:
        state["error"] = "Parser received empty input. No text to parse."
        state["agent_trace"].append({
            "agent": "Parser",
            "action": "failed",
            "output": "Empty extracted_text"
        })
        return state

    user_prompt = f"Parse this math problem:\n\n{extracted_text}"

    try:
        response = get_groq_client().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=600,
            temperature=0.1   # Low temperature for consistent structured output
        )

        raw_content = response.choices[0].message.content or ""

        # Use _safe_json_loads — handles LaTeX backslashes that crash json.loads
        try:
            parsed = _safe_json_loads(raw_content)
        except Exception:
            # Retry with explicit instruction to escape backslashes
            retry = get_groq_client().chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": (
                        "Parse this math problem. IMPORTANT: in all JSON string values "
                        "write every backslash as double-backslash so JSON stays valid. "
                        "Example: write \\\\int not \\int\n\n" + extracted_text
                    )}
                ],
                max_tokens=600, temperature=0.1
            )
            parsed = _safe_json_loads(retry.choices[0].message.content or "{}")

        # Validate required fields
        required_fields = ["problem_text", "topic", "variables", "constraints",
                           "needs_clarification", "clarification_reason"]
        for field in required_fields:
            if field not in parsed:
                raise ValueError(f"Missing field: {field}")

        # Enforce valid topic values
        valid_topics = {"algebra", "probability", "calculus", "linear_algebra", "unknown"}
        if parsed["topic"] not in valid_topics:
            parsed["topic"] = "unknown"
            parsed["needs_clarification"] = True

        state["parsed_problem"] = parsed
        state["topic"] = parsed["topic"]

        # Trigger HITL if parser says clarification needed
        if parsed.get("needs_clarification", False):
            state["needs_hitl"] = True
            state["hitl_reason"] = parsed.get("clarification_reason", "Problem needs clarification.")

        state["agent_trace"].append({
            "agent": "Parser",
            "action": "parsed",
            "output": f"Topic: {parsed['topic']} | Needs clarification: {parsed['needs_clarification']}"
        })

    except json.JSONDecodeError as e:
        # Graceful fallback: mark for HITL
        state["parsed_problem"] = {
            "problem_text": extracted_text,
            "topic": "unknown",
            "variables": [],
            "constraints": [],
            "needs_clarification": True,
            "clarification_reason": f"Parser could not structure the problem (JSON parse error: {str(e)})"
        }
        state["topic"] = "unknown"
        state["needs_hitl"] = True
        state["hitl_reason"] = "Parser could not structure the problem. Please confirm the problem statement."
        state["agent_trace"].append({
            "agent": "Parser",
            "action": "fallback",
            "output": f"JSON parse failed: {str(e)}"
        })

    except Exception as e:
        state["error"] = f"Parser Agent error: {str(e)}"
        state["agent_trace"].append({
            "agent": "Parser",
            "action": "error",
            "output": str(e)
        })

    return state