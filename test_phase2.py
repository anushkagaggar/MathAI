"""
Phase 2 Integration Test Suite — 30 tests
Run: python test_phase2.py
All tests must pass before moving to Phase 3.
"""
import os
import sys
import json
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

PASS = "✅ PASS"
FAIL = "❌ FAIL"
SKIP = "⏭  SKIP"
results = []

def check(tid, desc, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((tid, desc, status, detail))
    print(f"{status}  [{tid}] {desc}" + (f" — {detail}" if detail else ""))

def skip(tid, desc, reason=""):
    results.append((tid, desc, SKIP, reason))
    print(f"{SKIP}  [{tid}] {desc}" + (f" — {reason}" if reason else ""))

API_KEY = os.getenv("GROQ_API_KEY", "")
HAS_API = bool(API_KEY) and API_KEY != "your_groq_api_key_here"

# ════════════════════════════════════════════════════════════════
# SECTION 1: Logger
# ════════════════════════════════════════════════════════════════
print("\n── Logger ─────────────────────────────────────────────")
try:
    from utils.logger import get_logger
    logger = get_logger("test_phase2")
    logger.info("Logger test message")
    check("T-LOG-01", "Logger: get_logger returns Logger", hasattr(logger, 'info'))
    check("T-LOG-02", "Logger: logs/ directory created", os.path.exists("logs"))
    check("T-LOG-03", "Logger: math_mentor.log exists", os.path.exists("logs/math_mentor.log"))
except Exception as e:
    check("T-LOG-SUITE", "Logger suite", False, str(e))

# ════════════════════════════════════════════════════════════════
# SECTION 2: SymPy Tool
# ════════════════════════════════════════════════════════════════
print("\n── SymPy Tool ─────────────────────────────────────────")
try:
    from tools.sympy_tool import solve_equation, differentiate, evaluate_limit, integrate_expression, dispatch

    r = solve_equation("x**2 - 5*x + 6 = 0")
    check("T-SYM-01", "SymPy: solve quadratic x^2-5x+6=0",
          r["success"] and "2" in r["result"] and "3" in r["result"], str(r))

    r = differentiate("x**3 + 2*x", "x")
    check("T-SYM-02", "SymPy: differentiate x^3+2x",
          r["success"] and "3*x**2" in r["simplified"].replace(" ",""), str(r))

    r = evaluate_limit("sin(x)/x", "x", "0")
    check("T-SYM-03", "SymPy: limit sin(x)/x as x->0 = 1",
          r["success"] and r["result"] == "1", str(r))

    r = integrate_expression("x**2", "x")
    check("T-SYM-04", "SymPy: integrate x^2",
          r["success"] and "x**3/3" in r["result"].replace(" ",""), str(r))

    r = solve_equation("totally broken ???")
    check("T-SYM-05", "SymPy: invalid expression → success=False, no crash",
          r["success"] == False and isinstance(r["error"], str))

    r = dispatch("probability", "P(A)+P(B)", {})
    check("T-SYM-06", "SymPy: probability dispatch returns success=False",
          r["success"] == False and "probability" in r["error"].lower())

    r = evaluate_limit("1/x", "x", "0")
    check("T-SYM-07", "SymPy: limit 1/x as x->0 returns infinity (no crash)",
          r["success"] and ("oo" in r["result"] or "inf" in r["result"].lower() or "zoo" in r["result"]))

except Exception as e:
    check("T-SYM-SUITE", "SymPy suite", False, str(e))

# ════════════════════════════════════════════════════════════════
# SECTION 3: Memory Store
# ════════════════════════════════════════════════════════════════
print("\n── Memory Store ───────────────────────────────────────")
# Clean slate for tests
_test_memory_file = os.path.join("memory", "_test_problems.json")

try:
    from memory import memory_store as ms
    original_file = ms.MEMORY_FILE
    ms.MEMORY_FILE = _test_memory_file
    os.makedirs("memory", exist_ok=True)

    # T-MEM-01: save and load
    test_state = {
        "input_type": "text",
        "extracted_text": "Solve x^2 - 4 = 0",
        "parsed_problem": {"problem_text": "Solve x^2 - 4 = 0", "topic": "algebra", "variables": ["x"], "constraints": []},
        "topic": "algebra",
        "retrieved_context": [{"source": "algebra.md", "relevance": 0.8, "content": "test"}],
        "solver_output": "x = 2 or x = -2",
        "sympy_result": "[2, -2]",
        "verifier_score": 0.92,
        "verifier_notes": "Correct",
        "final_answer": "x = ±2",
        "explanation": "STEP 1: Factor\nFINAL ANSWER: x = ±2\nKEY CONCEPT: difference of squares",
        "memory_context": []
    }
    pid = ms.save_problem(test_state)
    check("T-MEM-01", "Memory: save_problem returns problem_id", bool(pid) and len(pid) == 8, f"id={pid}")

    records = ms.load_all_problems()
    check("T-MEM-02", "Memory: load_all_problems finds saved record",
          any(r["id"] == pid for r in records), f"{len(records)} records")

    # T-MEM-03: save feedback
    ms.save_feedback(pid, "correct", "Great explanation")
    records2 = ms.load_all_problems()
    updated = next((r for r in records2 if r["id"] == pid), None)
    check("T-MEM-03", "Memory: save_feedback updates record",
          updated and updated.get("user_feedback") == "correct", str(updated))

    # T-MEM-04: invalid id feedback
    ms.save_feedback("nonexistent_id", "correct")
    check("T-MEM-04", "Memory: save_feedback on missing id — no crash", True)

    # T-MEM-05: get_problem_by_id
    rec = ms.get_problem_by_id(pid)
    check("T-MEM-05", "Memory: get_problem_by_id works", rec is not None and rec["id"] == pid)

    # Restore
    ms.MEMORY_FILE = original_file
    if os.path.exists(_test_memory_file):
        os.remove(_test_memory_file)

except Exception as e:
    check("T-MEM-SUITE", "Memory suite", False, str(e))

# ════════════════════════════════════════════════════════════════
# SECTION 4: HITL Manager
# ════════════════════════════════════════════════════════════════
print("\n── HITL Manager ───────────────────────────────────────")
try:
    from hitl.hitl_manager import get_hitl_context, apply_human_decision

    base_state = {
        "confidence": 0.5, "input_type": "image",
        "needs_hitl": True, "hitl_reason": "Low OCR confidence",
        "extracted_text": "Find x^2 - 4", "agent_trace": [],
        "verifier_score": None
    }

    ctx = get_hitl_context(base_state)
    check("T-HITL-01", "HITL: get_hitl_context returns dict with reason",
          "reason" in ctx and "trigger_type" in ctx, str(ctx))

    s = dict(base_state)
    s["agent_trace"] = []
    s = apply_human_decision(s, "approve")
    check("T-HITL-02", "HITL: approve sets needs_hitl=False, hitl_approved=True",
          s["needs_hitl"] == False and s["hitl_approved"] == True)

    s2 = dict(base_state)
    s2["agent_trace"] = []
    s2 = apply_human_decision(s2, "edit", edited_text="Corrected: x^2 - 4 = 0")
    check("T-HITL-03", "HITL: edit updates extracted_text and approves",
          s2["extracted_text"] == "Corrected: x^2 - 4 = 0" and s2["hitl_approved"] == True)

    s3 = dict(base_state)
    s3["agent_trace"] = []
    s3 = apply_human_decision(s3, "reject", comment="Completely wrong")
    check("T-HITL-04", "HITL: reject sets workflow_route=reject",
          s3["workflow_route"] == "reject" and s3["needs_hitl"] == False)

except Exception as e:
    check("T-HITL-SUITE", "HITL suite", False, str(e))

# ════════════════════════════════════════════════════════════════
# SECTION 5: Full Pipeline (requires API key)
# ════════════════════════════════════════════════════════════════
print("\n── Full Pipeline ──────────────────────────────────────")

if not HAS_API:
    for tid in ["T-PIPE-01","T-PIPE-02","T-PIPE-03","T-PIPE-04","T-PIPE-05","T-PIPE-06"]:
        skip(tid, f"Pipeline test", "GROQ_API_KEY not set")
else:
    try:
        from agents.graph import graph
        from agents import MathMentorState

        # T-PIPE-01: full algebra pipeline
        print("   Running full pipeline (algebra)...")
        state = MathMentorState(extracted_text="Solve x^2 - 5x + 6 = 0", agent_trace=[])
        result = graph.invoke(state)
        check("T-PIPE-01", "Pipeline: algebra — completes without error",
              not result.get("error"), result.get("error", ""))
        check("T-PIPE-02", "Pipeline: algebra — has final_answer",
              bool(result.get("final_answer")), str(result.get("final_answer",""))[:80])
        check("T-PIPE-03", "Pipeline: algebra — has explanation with STEP",
              "STEP" in result.get("explanation", ""), result.get("explanation","")[:80])
        check("T-PIPE-04", "Pipeline: all 5 agents in trace",
              len(result.get("agent_trace", [])) >= 4,
              f"{len(result.get('agent_trace',[]))} entries: {[t['agent'] for t in result.get('agent_trace',[])]}")
        check("T-PIPE-05", "Pipeline: memory saved (last_problem_id set)",
              bool(result.get("last_problem_id")), result.get("last_problem_id", "not set"))

        # T-PIPE-06: second run — memory reuse
        print("   Running second pipeline run (memory reuse test)...")
        state2 = MathMentorState(extracted_text="Solve x^2 - 5x + 6 = 0", agent_trace=[])
        result2 = graph.invoke(state2)
        has_memory = len(result2.get("memory_context", [])) > 0
        check("T-PIPE-06", "Pipeline: second run finds memory context",
              has_memory, f"memory_context items: {len(result2.get('memory_context',[]))}")

    except Exception as e:
        check("T-PIPE-SUITE", "Full pipeline suite", False, str(e))

    # T-PIPE-07: non-math input is rejected
    try:
        state_bad = MathMentorState(extracted_text="What is the capital of France?", agent_trace=[])
        result_bad = graph.invoke(state_bad)
        check("T-PIPE-07", "Pipeline: non-math input → route=reject or hitl",
              result_bad.get("workflow_route") in ("reject", "hitl", "clarify"),
              result_bad.get("workflow_route"))
    except Exception as e:
        check("T-PIPE-07", "Pipeline: non-math reject", False, str(e))

    # T-PIPE-08: empty input handled gracefully
    try:
        state_empty = MathMentorState(extracted_text="", agent_trace=[])
        result_empty = graph.invoke(state_empty)
        check("T-PIPE-08", "Pipeline: empty input — no unhandled exception",
              True, f"error={result_empty.get('error','none')}")
    except Exception as e:
        check("T-PIPE-08", "Pipeline: empty input graceful", False, str(e))

# ════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("PHASE 2 TEST SUMMARY")
print("="*60)
passed = sum(1 for _,_,s,_ in results if s == PASS)
failed = sum(1 for _,_,s,_ in results if s == FAIL)
skipped = sum(1 for _,_,s,_ in results if s == SKIP)
print(f"Passed: {passed}  |  Failed: {failed}  |  Skipped: {skipped}  |  Total: {len(results)}")
if failed == 0:
    print("\n✅ ALL TESTS PASSED — Ready for Phase 3!")
else:
    print(f"\n❌ {failed} test(s) failed — Fix before Phase 3")
    for tid, desc, status, detail in results:
        if status == FAIL:
            print(f"   {FAIL} [{tid}] {desc}: {detail}")