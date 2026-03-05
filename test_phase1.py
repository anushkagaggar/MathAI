"""
Phase 1 Integration Test Script
Run: python test_phase1.py
All tests must pass before moving to Phase 2.
"""

import os
import sys
import json

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []

def check(test_id, description, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((test_id, description, status, detail))
    print(f"{status}  [{test_id}] {description}" + (f" — {detail}" if detail else ""))


# ══════════════════════════════════════════════════════════════
# SECTION 1: Utils
# ══════════════════════════════════════════════════════════════
print("\n── Utils ──────────────────────────────────────────────")

from utils.formatting import normalize_math_text, clean_whitespace
from utils.confidence import estimate_ocr_confidence, estimate_asr_confidence, is_below_threshold

t = normalize_math_text("find the square root of 144")
check("T-UTIL-01", "normalize: square root of X", "sqrt(144)" in t, t)

t = normalize_math_text("x squared plus 3x equals 0")
check("T-UTIL-02", "normalize: squared → ^2", "^2" in t, t)

t = normalize_math_text("dy by dx of x cubed")
check("T-UTIL-03", "normalize: dy by dx", "dy/dx" in t or "d/dx" in t, t)

score = estimate_ocr_confidence("Find x^2 + 3x = 0")
check("T-UTIL-04", "OCR confidence: clean text >= 0.5", score >= 0.5, f"score={score}")

score = estimate_ocr_confidence("@@@###$$$???")
check("T-UTIL-05", "OCR confidence: garbled text < 0.5", score < 0.5, f"score={score}")

score = estimate_asr_confidence("[BLANK_AUDIO]")
check("T-UTIL-06", "ASR confidence: blank audio = 0.1", score <= 0.15, f"score={score}")

score = estimate_asr_confidence("find the derivative of x squared")
check("T-UTIL-07", "ASR confidence: math transcript >= 0.7", score >= 0.7, f"score={score}")

# ══════════════════════════════════════════════════════════════
# SECTION 2: Input Processors
# ══════════════════════════════════════════════════════════════
print("\n── Input Processors ───────────────────────────────────")

from input_processing.text_processor import process_text

r = process_text("Solve x^2 - 5x + 6 = 0")
check("T-IP-01", "text: clean problem", r["confidence"] == 1.0 and r["needs_hitl"] == False, str(r["text"][:40]))

r = process_text("find the square root of 144")
check("T-IP-02", "text: spoken math normalized", "sqrt" in r["text"].lower() or "144" in r["text"], r["text"])

r = process_text("")
check("T-IP-03", "text: empty triggers HITL", r["needs_hitl"] == True, "empty input")

# Image and audio tests require actual API calls — skipped in offline test
print("   ⏭  T-IP-04 (image) — skipped: requires Groq API + image file")
print("   ⏭  T-IP-05 (audio) — skipped: requires Groq API + audio file")

# ══════════════════════════════════════════════════════════════
# SECTION 3: RAG Pipeline
# ══════════════════════════════════════════════════════════════
print("\n── RAG Pipeline ───────────────────────────────────────")

if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "your_groq_api_key_here":
    print("   ⚠️  GROQ_API_KEY not set — RAG embedding tests will still run (uses local HF model)")

try:
    from rag.vector_store import build_vector_store, load_vector_store
    print("   Building FAISS index (first run downloads ~80MB embedding model)...")
    store = build_vector_store()
    check("T-RAG-01", "RAG: build_vector_store() succeeds", store is not None)

    store2 = load_vector_store()
    check("T-RAG-02", "RAG: load_vector_store() succeeds", store2 is not None)

    from rag.retriever import retrieve
    results_algebra = retrieve("quadratic formula", k=4)
    check("T-RAG-03", "RAG: algebra query returns results", len(results_algebra) > 0,
          f"{len(results_algebra)} chunks, top source: {results_algebra[0]['source'] if results_algebra else 'none'}")

    results_prob = retrieve("P(A union B) addition rule", k=4)
    check("T-RAG-04", "RAG: probability query returns results", len(results_prob) > 0,
          f"top source: {results_prob[0]['source'] if results_prob else 'none'}")

    results_calc = retrieve("derivative of x^3 power rule", k=4)
    check("T-RAG-05", "RAG: calculus query returns results", len(results_calc) > 0,
          f"top source: {results_calc[0]['source'] if results_calc else 'none'}")

    # All results must have source key
    all_have_source = all("source" in r for r in results_algebra + results_prob + results_calc)
    check("T-RAG-06", "RAG: all results have source attribution", all_have_source)

    # Non-math query should not crash
    results_irrelevant = retrieve("best pizza recipe", k=4)
    check("T-RAG-07", "RAG: irrelevant query doesn't crash", isinstance(results_irrelevant, list))

except Exception as e:
    check("T-RAG-BUILD", "RAG pipeline", False, str(e))

# ══════════════════════════════════════════════════════════════
# SECTION 4: Agents (require GROQ_API_KEY)
# ══════════════════════════════════════════════════════════════
print("\n── Agents ─────────────────────────────────────────────")

api_key = os.getenv("GROQ_API_KEY", "")
if not api_key or api_key == "your_groq_api_key_here":
    print("   ⚠️  GROQ_API_KEY not configured — skipping LLM agent tests")
    print("   ⏭  T-AGT-01 through T-AGT-10 skipped: set GROQ_API_KEY in .env")
else:
    try:
        from agents.parser_agent import parser_node
        from agents.intent_router_agent import intent_router_node
        from agents import MathMentorState

        # T-AGT-01: clean algebra
        state = MathMentorState(extracted_text="Solve x^2 - 5x + 6 = 0", agent_trace=[])
        state = parser_node(state)
        check("T-AGT-01", "Parser: algebra problem", 
              state.get("parsed_problem", {}).get("topic") == "algebra",
              str(state.get("parsed_problem", {})))

        # T-AGT-02: ambiguous input
        state2 = MathMentorState(extracted_text="solve x", agent_trace=[])
        state2 = parser_node(state2)
        check("T-AGT-02", "Parser: ambiguous → needs_clarification",
              state2.get("parsed_problem", {}).get("needs_clarification") == True,
              str(state2.get("parsed_problem", {})))

        # T-AGT-03: non-math input
        state3 = MathMentorState(extracted_text="What is the capital of France?", agent_trace=[])
        state3 = parser_node(state3)
        check("T-AGT-03", "Parser: non-math → topic=unknown",
              state3.get("parsed_problem", {}).get("topic") == "unknown",
              str(state3.get("parsed_problem", {})))

        # T-AGT-04: empty input
        state4 = MathMentorState(extracted_text="", agent_trace=[])
        state4 = parser_node(state4)
        check("T-AGT-04", "Parser: empty input → error set",
              bool(state4.get("error")), state4.get("error", ""))

        # T-AGT-05: router — solve route
        state5 = MathMentorState(
            extracted_text="Find dy/dx of x^3",
            needs_hitl=False,
            agent_trace=[],
            parsed_problem={"topic": "calculus", "needs_clarification": False, "clarification_reason": ""}
        )
        state5 = intent_router_node(state5)
        check("T-AGT-05", "Router: valid problem → route=solve",
              state5.get("workflow_route") == "solve", state5.get("workflow_route"))

        # T-AGT-06: router — HITL route
        state6 = MathMentorState(needs_hitl=True, hitl_reason="low confidence", agent_trace=[])
        state6 = intent_router_node(state6)
        check("T-AGT-06", "Router: needs_hitl=True → route=hitl",
              state6.get("workflow_route") == "hitl", state6.get("workflow_route"))

        # T-AGT-07: router — reject
        state7 = MathMentorState(
            needs_hitl=False, agent_trace=[],
            parsed_problem={"topic": "unknown", "needs_clarification": False}
        )
        state7 = intent_router_node(state7)
        check("T-AGT-07", "Router: unknown topic → route=reject",
              state7.get("workflow_route") == "reject", state7.get("workflow_route"))

        # T-AGT-08: Full graph run
        from agents.graph import graph
        init_state = MathMentorState(extracted_text="Find the roots of x^2 - 4 = 0", agent_trace=[])
        final_state = graph.invoke(init_state)
        check("T-AGT-08", "Full graph: runs without exception", True)
        check("T-AGT-09", "Full graph: has parsed_problem", bool(final_state.get("parsed_problem")))
        check("T-AGT-10", "Full graph: agent_trace has entries", len(final_state.get("agent_trace", [])) >= 2,
              f"{len(final_state.get('agent_trace', []))} entries")

    except Exception as e:
        check("T-AGT-SUITE", "Agent test suite", False, str(e))

# ══════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("PHASE 1 TEST SUMMARY")
print("="*60)
passed = sum(1 for _, _, s, _ in results if s == PASS)
failed = sum(1 for _, _, s, _ in results if s == FAIL)
print(f"Passed: {passed}  |  Failed: {failed}  |  Total: {len(results)}")
if failed == 0:
    print("\n✅ ALL TESTS PASSED — Ready for Phase 2!")
else:
    print(f"\n❌ {failed} test(s) failed — Fix before Phase 2")
    for tid, desc, status, detail in results:
        if status == FAIL:
            print(f"   {FAIL} [{tid}] {desc}: {detail}")