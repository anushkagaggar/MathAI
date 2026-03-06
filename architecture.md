# Math Mentor — System Architecture

```mermaid
flowchart TD
    UI[🖥️ Streamlit UI] --> INPUT[Input Processing Layer]
    INPUT --> |text| TP[Text Processor]
    INPUT --> |image| IP[Image Processor\nGroq Vision]
    INPUT --> |audio| AP[Audio Processor\nGroq Whisper]
    TP & IP & AP --> CONF{Confidence\nCheck}
    CONF --> |low confidence| HITL1[🔵 HITL Review #1\nOCR / ASR correction]
    CONF --> |ok| PA[🔍 Parser Agent\nLLaMA 3.3-70b]
    HITL1 --> PA
    PA --> |needs clarification| HITL2[🔵 HITL Review #2\nClarification]
    PA --> IR[🔀 Intent Router Agent]
    IR --> |reject| END1[❌ End — Not in scope]
    IR --> |solve| SA[🧮 Solver Agent]
    SA --> RAG[(📖 FAISS RAG Index\nalgebra/calc/prob/linalg)]
    SA --> MEM[(🧠 Memory FAISS\nPast solved problems)]
    SA --> SYM[🔢 SymPy Tool\nGround-truth math]
    SA --> LLM1[☁️ Groq LLaMA 3.3\nStep-by-step solve]
    SA --> VA[✅ Verifier Agent]
    VA --> |score < threshold| HITL3[🔵 HITL Review #3\nSolution correction]
    VA --> |score ≥ threshold| EA[📝 Explainer Agent\nLLaMA 3.3-70b]
    HITL3 --> EA
    EA --> RESULT[🎯 Final Answer\n+ Explanation]
    EA --> SAVE[💾 Save to Memory\nJSON + FAISS]
    RESULT --> FB[👍👎 User Feedback]
    FB --> SAVE
```

## Component Summary

| Component | File | Role |
|-----------|------|------|
| Streamlit UI | `app.py` | Full UI, HITL panels, session state |
| Text Processor | `input_processing/text_processor.py` | Passthrough with confidence=1.0 |
| Image Processor | `input_processing/image_processor.py` | Groq Vision OCR |
| Audio Processor | `input_processing/audio_processor.py` | Groq Whisper ASR |
| Parser Agent | `agents/parser_agent.py` | Extracts problem structure → JSON |
| Intent Router | `agents/intent_router_agent.py` | Routes: solve/hitl/clarify/reject |
| Solver Agent | `agents/solver_agent.py` | RAG + SymPy + LLM solving |
| Verifier Agent | `agents/verifier_agent.py` | Critiques solution, assigns score |
| Explainer Agent | `agents/explainer_agent.py` | Step-by-step student explanation |
| HITL Manager | `hitl/hitl_manager.py` | approve/edit/reject state transitions |
| Memory Store | `memory/memory_store.py` | JSON persistence of all problems |
| Memory Retriever | `memory/memory_retriever.py` | FAISS similarity search over past problems |
| SymPy Tool | `tools/sympy_tool.py` | Symbolic math ground truth |
| RAG Vector Store | `rag/` | FAISS index over knowledge base |
| LangGraph Pipeline | `agents/graph.py` | Orchestrates all 5 nodes |