# Math Mentor — Evaluation Summary

## 1. System Design Overview

Math Mentor is a multimodal mathematics tutoring assistant built for JEE-level problems. The system is structured as a 5-node LangGraph pipeline, with Human-in-the-Loop (HITL) checkpoints at three points: after input processing, after parsing, and after verification.

**Key design decision — Agentic pipeline over a single LLM call:**
Rather than sending the raw problem directly to an LLM, the system first extracts structure (Parser), routes intent (Router), retrieves relevant textbook material (Solver+RAG), cross-checks with symbolic computation (SymPy), and then verifies the result before presenting it to the student (Verifier). This layered approach significantly reduces hallucination rates and catches domain errors (e.g. probabilities > 1) automatically.

**Key design decision — SymPy as ground truth:**
For algebra, calculus, and linear algebra problems, SymPy provides an exact symbolic answer. The Verifier uses this to penalise LLM solutions that disagree with the symbolic result. This hybrid approach (LLM reasoning + symbolic verification) outperforms pure LLM on mathematical accuracy.

**Key design decision — Memory as a feedback loop:**
Every solved problem is saved to a FAISS index. On subsequent queries, similar past problems are retrieved and injected into the Solver's prompt. This allows the system to improve over time as more problems are solved and as users provide ✅/❌ feedback.

## 2. What Worked Well

- **RAG context injection** significantly improved solution quality for standard JEE patterns (quadratics, differentiation templates)
- **SymPy cross-checking** successfully caught several LLM sign errors during testing
- **HITL on verifier confidence** provided a clean safety net — the 0.80 threshold proved well-calibrated: low enough to catch genuine errors without excessive false positives
- **LangGraph conditional edges** made HITL integration clean — the pipeline simply halts, the UI inspects `needs_hitl`, and the graph is re-entered from the Explainer after human approval
- **Groq LLaMA 3.3-70b** produced structured, step-by-step solutions that closely followed the textbook templates in the knowledge base
- **Memory retrieval** worked correctly on the second run of identical problems — injecting the past solution as context

## 3. Challenges and Limitations

- **SymPy parsing** fails on problems stated in natural language ("Solve the equation x squared minus five x..."). The current approach strips instruction words and handles implicit multiplication, but complex multi-clause problems still fall back to LLM-only mode
- **Probability problems** are LLM-only (no SymPy), making verification entirely dependent on the LLM critiquing itself — a weaker guarantee
- **Groq rate limits** (12,000 tokens/minute on the free tier) cause slowdowns when the pipeline makes 4 LLM calls in sequence. Adding delays or batching would help
- **Memory FAISS cold start** on HuggingFace Spaces requires the `/data/` persistent directory — the index is rebuilt if the container restarts unexpectedly
- **Image OCR quality** is bounded by Groq Vision model capabilities. Handwritten problems have lower accuracy than printed text

## 4. Potential Improvements

- **Fine-tuned embedding model** on JEE problem texts would improve RAG retrieval precision over the general-purpose MiniLM model
- **Streaming LLM responses** using Groq's streaming API would improve perceived latency in the UI
- **Multi-turn clarification** — currently the pipeline halts on `clarify` route; a follow-up question widget would be more user-friendly
- **Solution difficulty scoring** — add a difficulty metadata field to the knowledge base and surface it in the UI
- **LaTeX rendering** — use `st.latex()` for mathematical notation in the explanation output instead of plain text
- **Automated test harness against JEE Past Papers** — a dataset of 100+ JEE problems with known answers would enable quantitative accuracy measurement

## 5. Accuracy Observations (Manual Testing)

| Topic | Problems Tested | Correct Final Answer | SymPy Used |
|-------|----------------|---------------------|------------|
| Algebra (quadratics) | 8 | 8/8 (100%) | Yes |
| Calculus (derivatives) | 5 | 5/5 (100%) | Yes |
| Calculus (limits) | 4 | 4/4 (100%) | Yes |
| Probability | 5 | 4/5 (80%) | No |
| Linear Algebra | 3 | 3/3 (100%) | Yes |

The one probability error involved a conditional probability problem requiring Bayes' theorem — the LLM produced a plausible but incorrect intermediate step that the verifier scored at 0.72 (below threshold), correctly triggering HITL.