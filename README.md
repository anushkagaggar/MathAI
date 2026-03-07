---
title: Math Mentor
emoji: 🧠
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8501
pinned: false
---

# 🧠 Math Mentor

> AI-powered multimodal JEE mathematics solver with 5 LangGraph agents, RAG, HITL, and self-improving memory.

---

## 🎥 Demo Video
*[Link to be added after recording]*

## 🌐 Live Demo
[*\[HuggingFace Spaces URL\]*](https://gaggaranushka-mathmentor.hf.space/)

---

## ✨ Features

- **Multimodal Input** — Text, image (OCR via Groq Vision), audio (ASR via Groq Whisper)
- **5-Agent Pipeline** — Parser → Router → Solver → Verifier → Explainer (LangGraph)
- **RAG Knowledge Base** — FAISS index over algebra, calculus, probability, linear algebra textbooks
- **SymPy Verification** — Ground-truth symbolic math cross-checks LLM answers
- **Human-in-the-Loop (HITL)** — 3 trigger points: low OCR/ASR confidence, low verifier score
- **Self-Improving Memory** — FAISS + JSON store of past solved problems; similar problems injected as context
- **User Feedback Loop** — ✅/❌ buttons update memory for continuous improvement

---

## 🏗️ Architecture

See [`architecture.md`](architecture.md) for the full Mermaid diagram.

```
Text/Image/Audio → Input Processing → Parser → Router
                                                  ↓ solve
                                             Solver (RAG + SymPy + LLM)
                                                  ↓
                                             Verifier (score + HITL gate)
                                                  ↓ score ≥ 0.80
                                             Explainer → Final Answer + Memory
```

---

## 🛠️ Tech Stack

| Library | Version | Purpose |
|---------|---------|---------|
| streamlit | latest | Web UI |
| langgraph | latest | Agent orchestration |
| langchain-huggingface | latest | HuggingFace embeddings |
| groq | latest | LLaMA 3.3-70b + Whisper + Vision |
| sympy | latest | Symbolic math ground truth |
| faiss-cpu | latest | RAG + Memory vector search |
| sentence-transformers | latest | Text embeddings |
| pydub | latest | Audio format conversion |
| python-dotenv | latest | Environment variables |

---

## ⚙️ Environment Variables

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `GROQ_API_KEY` | Groq API key for LLM calls | [console.groq.com](https://console.groq.com) |
| `GROQ_LLM_MODEL` | LLM model name | Default: `llama-3.3-70b-versatile` |
| `GROQ_VISION_MODEL` | Vision model for OCR | Default: `llama-4-scout-17b-16e-instruct` |
| `GROQ_AUDIO_MODEL` | Whisper model for ASR | Default: `whisper-large-v3` |
| `VERIFIER_CONFIDENCE_THRESHOLD` | Score below which HITL triggers | Default: `0.80` |
| `OCR_CONFIDENCE_THRESHOLD` | OCR confidence below which HITL triggers | Default: `0.75` |
| `ASR_CONFIDENCE_THRESHOLD` | ASR confidence below which HITL triggers | Default: `0.75` |
| `DEBUG` | Enable DEBUG logging | `true` or `false` |

---

## 🚀 Setup (Local)

```bash
# 1. Clone
git clone https://github.com/your-username/math-mentor.git
cd math-mentor

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 5. Run
streamlit run app.py
```

---

## 📁 Project Structure

```
math-mentor/
├── app.py                    # Streamlit UI (Phase 3)
├── requirements.txt
├── packages.txt              # System deps for HF Spaces
├── .env.example
├── architecture.md           # Mermaid system diagram
├── README.md
│
├── agents/
│   ├── __init__.py           # MathMentorState TypedDict
│   ├── graph.py              # LangGraph pipeline
│   ├── parser_agent.py
│   ├── intent_router_agent.py
│   ├── solver_agent.py
│   ├── verifier_agent.py
│   └── explainer_agent.py
│
├── input_processing/
│   ├── image_processor.py    # Groq Vision OCR
│   ├── audio_processor.py    # Groq Whisper ASR
│   └── text_processor.py
│
├── hitl/
│   └── hitl_manager.py       # HITL state transitions
│
├── memory/
│   ├── memory_store.py       # JSON persistence
│   └── memory_retriever.py   # FAISS similarity search
│
├── rag/
│   ├── embedder.py
│   ├── vector_store.py
│   ├── retriever.py
│   └── knowledge_base/       # Markdown textbook files
│
├── tools/
│   └── sympy_tool.py         # Symbolic math engine
│
└── utils/
    ├── logger.py
    ├── confidence.py
    └── formatting.py
```

---

## 🧪 Running Tests

```bash
# Phase 1 tests (27 tests)
python test_phase1.py

# Phase 2 tests (27 tests — requires GROQ_API_KEY for pipeline tests)
python test_phase2.py
```

---

## 🚢 Deploy to HuggingFace Spaces

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) → **New Space**
2. SDK: **Streamlit**, Visibility: **Public**, Hardware: **CPU basic (free)**
3. Connect your GitHub repo under **Settings → Repository**
4. Add secret: **Settings → Variables and Secrets → GROQ_API_KEY**
5. Push to `main` — HF auto-deploys on every push

> **Note:** The RAG FAISS index rebuilds on cold start. Memory (`/data/memory/`) persists between deploys.

---

## 📚 Scope

Topics covered: **Algebra**, **Probability**, **Calculus**, **Linear Algebra**

Exam scope: **JEE Mains / JEE Advanced** difficulty

---

## ⚠️ Known Limitations

- SymPy may fail on highly complex multi-step expressions
- Groq free tier has rate limits (~30 req/min)
- Audio transcription accuracy depends on recording quality
- Image OCR works best on clear, printed text

---

## 📄 License

MIT — see [LICENSE](LICENSE)