import os
import json
from groq import Groq
from utils.groq_client import get_groq_client
from dotenv import load_dotenv
from agents import MathMentorState
from utils.logger import get_logger

logger = get_logger(__name__)

load_dotenv()

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

        # Strip any accidental markdown fences
        clean_content = raw_content.strip()
        if clean_content.startswith("```"):
            clean_content = clean_content.split("```")[1]
            if clean_content.startswith("json"):
                clean_content = clean_content[4:]
        clean_content = clean_content.strip()

        parsed = json.loads(clean_content)

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