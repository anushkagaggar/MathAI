import os
from groq import Groq
from dotenv import load_dotenv
from utils.logger import get_logger
from agents import MathMentorState

load_dotenv()

logger = get_logger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
LLM_MODEL = os.getenv("GROQ_LLM_MODEL", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = """You are an expert JEE mathematics tutor. Solve the given problem step by step.

You have access to: retrieved textbook context, a SymPy computed result (if available), and similar past solved problems (if available).

Rules:
1. Show EVERY step clearly with brief reasoning.
2. If a SymPy result is provided, your final numerical answer MUST match it exactly.
3. Only cite sources that appear in Retrieved Context — never invent references.
4. If you cannot solve it confidently, state explicitly: "I cannot solve this confidently."
5. Use clear mathematical notation. Prefer plain text math (x^2, sqrt(x), etc.)."""


def _build_user_prompt(state: MathMentorState) -> str:
    parsed = state.get("parsed_problem", {})
    topic = state.get("topic", "unknown")
    retrieved = state.get("retrieved_context", [])
    memory_ctx = state.get("memory_context", [])
    sympy_result = state.get("sympy_result", "")

    lines = [
        f"Problem: {parsed.get('problem_text', state.get('extracted_text', ''))}",
        f"Topic: {topic}",
        f"Variables: {', '.join(parsed.get('variables', []))}",
        f"Constraints: {', '.join(parsed.get('constraints', []))}",
        ""
    ]

    # RAG context
    if retrieved:
        lines.append("Retrieved Context:")
        for chunk in retrieved:
            lines.append(f"[SOURCE: {chunk['source']}]\n{chunk['content']}")
            lines.append("")
    else:
        lines.append("Retrieved Context: None available — solve from general knowledge.")
        lines.append("")

    # SymPy result
    if sympy_result and sympy_result != "Not available":
        lines.append(f"SymPy Computed Result: {sympy_result}")
        lines.append("(Your final answer MUST match this.)")
        lines.append("")

    # Memory context
    if memory_ctx:
        lines.append("Similar Past Solved Problems:")
        for mem in memory_ctx:
            lines.append(f"[PAST PROBLEM] Q: {mem.get('problem_text', '')[:120]}")
            lines.append(f"[PAST ANSWER]  A: {mem.get('answer', '')[:200]}")
            lines.append("")

    lines.append("Now solve the problem step by step:")
    return "\n".join(lines)


def solver_node(state: MathMentorState) -> MathMentorState:
    """
    LangGraph node: Retrieves RAG + memory context, runs SymPy,
    calls Groq LLaMA to produce a full solution.
    """
    state.setdefault("agent_trace", [])
    state.setdefault("retrieved_context", [])
    state.setdefault("memory_context", [])

    parsed = state.get("parsed_problem", {})
    if not parsed:
        state["error"] = "Solver received no parsed_problem"
        logger.error("Solver: no parsed_problem in state")
        return state

    problem_text = parsed.get("problem_text", state.get("extracted_text", ""))
    topic = state.get("topic", "unknown")

    # ── Step 1: Memory retrieval ────────────────────────────────
    try:
        from memory.memory_retriever import retrieve_similar
        memory_ctx = retrieve_similar(problem_text)
        state["memory_context"] = memory_ctx
        if memory_ctx:
            logger.info("Solver: found %d similar past problems in memory", len(memory_ctx))
        else:
            logger.debug("Solver: no memory context found")
    except Exception as e:
        logger.warning("Solver: memory retrieval failed: %s", str(e))
        state["memory_context"] = []

    # ── Step 2: RAG retrieval ───────────────────────────────────
    try:
        from rag.retriever import retrieve_with_fallback
        retrieved = retrieve_with_fallback(problem_text)
        state["retrieved_context"] = retrieved
        sources = list({r["source"] for r in retrieved})
        logger.info("Solver: RAG retrieved %d chunks from: %s", len(retrieved), sources)
    except Exception as e:
        logger.warning("Solver: RAG retrieval failed: %s", str(e))
        state["retrieved_context"] = []

    # ── Step 3: SymPy computation ───────────────────────────────
    sympy_result_str = "Not available"
    try:
        from tools.sympy_tool import dispatch
        sympy_out = dispatch(topic, problem_text, parsed)
        if sympy_out.get("success"):
            sympy_result_str = sympy_out["result"]
            state["sympy_result"] = sympy_result_str
            logger.info("Solver: SymPy result: %s", sympy_result_str[:100])
        else:
            logger.debug("Solver: SymPy not applicable: %s", sympy_out.get("error", ""))
            state["sympy_result"] = ""
    except Exception as e:
        logger.warning("Solver: SymPy dispatch failed: %s", str(e))
        state["sympy_result"] = ""

    # ── Step 4: Build and send LLM prompt ──────────────────────
    user_prompt = _build_user_prompt(state)

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt}
            ],
            max_tokens=2000,
            temperature=0.2
        )

        solver_output = response.choices[0].message.content or ""

        if not solver_output.strip():
            solver_output = "The solver could not produce a response. Please try rephrasing the problem."
            logger.warning("Solver: LLM returned empty response")
        else:
            usage = response.usage
            logger.info("Solver: LLM completed. Tokens used — prompt: %d, completion: %d",
                        usage.prompt_tokens, usage.completion_tokens)

        state["solver_output"] = solver_output

    except Exception as e:
        logger.error("Solver: Groq API call failed: %s", str(e))
        state["solver_output"] = f"Solver error: {str(e)}"
        state["error"] = f"Solver API error: {str(e)}"
        return state

    # ── Step 5: Update trace ────────────────────────────────────
    rag_sources = list({r["source"] for r in state.get("retrieved_context", [])})
    state["agent_trace"].append({
        "agent": "Solver",
        "action": "solved",
        "output": (
            f"RAG sources: {rag_sources} | "
            f"SymPy: {'✓ ' + sympy_result_str[:40] if sympy_result_str != 'Not available' else '✗ not used'} | "
            f"Memory hits: {len(state.get('memory_context', []))}"
        )
    })

    return state