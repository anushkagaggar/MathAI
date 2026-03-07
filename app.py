"""
Math Mentor — Phase 3 Streamlit UI
Multimodal JEE math solver: Text / Image / Audio
5 LangGraph agents + HITL + RAG + Memory
KaTeX math rendering throughout
"""
import os, sys, time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Math Mentor",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ROOT)

from utils.logger import get_logger
from agents.graph import graph
from agents import MathMentorState
from memory.memory_store import save_feedback, load_all_problems
from hitl.hitl_manager import get_hitl_context, apply_human_decision

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CSS + KaTeX
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<link rel="stylesheet"
  href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css"
  crossorigin="anonymous">
<script defer
  src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"
  crossorigin="anonymous"></script>
<script defer
  src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
  crossorigin="anonymous"
  onload="renderMathInElement(document.body, {
    delimiters: [
      {left: '$$', right: '$$', display: true},
      {left: '$',  right: '$',  display: false},
      {left: '\\\\(', right: '\\\\)', display: false},
      {left: '\\\\[', right: '\\\\]', display: true}
    ],
    throwOnError: false
  });"></script>

<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Agent badges */
.badge { display:inline-block; padding:2px 10px; border-radius:999px;
         font-size:11px; font-weight:600; margin-right:4px; letter-spacing:.3px; }
.bp { background:rgba(59,130,246,0.2);  color:#93C5FD; }
.br { background:rgba(139,92,246,0.2);  color:#C4B5FD; }
.bs { background:rgba(34,197,94,0.2);   color:#86EFAC; }
.bv { background:rgba(234,179,8,0.2);   color:#FDE047; }
.be { background:rgba(20,184,166,0.2);  color:#5EEAD4; }

/* Math preview box — shown above raw-text editor */
.math-preview {
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 6px;
    font-size: 16px;
    line-height: 1.8;
    color: inherit;
    overflow-x: auto;
}
.math-preview-label {
    font-size: 11px; font-weight: 600; letter-spacing: .5px;
    text-transform: uppercase; opacity: 0.55; margin-bottom: 4px;
}

/* Answer box */
.answer-box {
    background: rgba(22,163,74,0.12);
    border-left: 4px solid #16A34A; border-radius: 8px;
    padding: 16px 20px; margin: 10px 0;
    font-size: 16px; line-height: 1.9;
    color: inherit; overflow-x: auto;
}
.answer-label {
    font-size: 11px; font-weight:700; letter-spacing:.5px;
    text-transform:uppercase; color:#16A34A; margin-bottom:6px;
}

/* Step lines */
.step-block {
    padding: 8px 0 8px 0;
    border-bottom: 1px solid rgba(148,163,184,0.15);
    line-height: 1.8; color: inherit; overflow-x: auto;
}
.step-header {
    font-weight: 700; font-size: 13px; letter-spacing: .3px;
    text-transform: uppercase; opacity: 0.7; margin-bottom: 2px;
}
.final-block {
    background: rgba(22,163,74,0.13);
    border-left: 3px solid #16A34A; border-radius: 6px;
    padding: 10px 16px; margin: 10px 0;
    font-weight: 600; font-size: 16px;
    line-height: 1.8; color: inherit; overflow-x: auto;
}
.key-block {
    background: rgba(37,99,235,0.10);
    border-left: 3px solid #3B82F6; border-radius: 6px;
    padding: 10px 16px; margin: 10px 0;
    line-height: 1.8; color: inherit; overflow-x: auto;
}

/* Confidence */
.conf-g { color:#16A34A; font-weight:700; }
.conf-y { color:#D97706; font-weight:700; }
.conf-r { color:#DC2626; font-weight:700; }

/* Step-by-step explanation lines */
.step-line {
    padding: 5px 0;
    border-bottom: 1px solid rgba(148,163,184,0.2);
    color: inherit;
    line-height: 1.7;
}
.final-line {
    background: rgba(22,163,74,0.12);
    border-left: 3px solid #16A34A; border-radius: 6px;
    padding: 8px 14px; margin: 8px 0;
    font-weight: 700; color: inherit;
}
.key-line {
    background: rgba(37,99,235,0.10);
    border-left: 3px solid #3B82F6; border-radius: 6px;
    padding: 8px 14px; margin: 8px 0;
    color: inherit;
}

/* ── Light mode ONLY: fix grey text — dark mode untouched ── */
@media (prefers-color-scheme: light) {
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] .stRadio label,
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span,
  [data-testid="stSidebar"] .stSlider label { color: #111827 !important; font-weight: 500 !important; }

  [data-testid="stMetricLabel"] p,
  [data-testid="stMetricValue"] { color: #111827 !important; font-weight: 600 !important; }

  .stCaption, [data-testid="stCaptionContainer"] p, small, .stCaption p {
    color: #374151 !important; font-weight: 500 !important;
  }

  .stTextArea label, .stTextInput label, .stFileUploader label {
    color: #111827 !important; font-weight: 600 !important;
  }

  .streamlit-expanderHeader, [data-testid="stExpanderToggleIcon"] + div {
    color: #111827 !important; font-weight: 600 !important;
  }

  table td, table th { color: #111827 !important; }

  [data-testid="stAlert"] p { color: #111827 !important; font-weight: 500 !important; }

  .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown li {
    color: #111827 !important;
  }

  [data-testid="stDividerText"] { color: #374151 !important; }
  [data-testid="stSidebar"] hr { border-color: #d1d5db !important; }
  .stRadio div[role="radiogroup"] label span { color: #111827 !important; }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 1. SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS = {
    "graph_state": None,
    "awaiting_hitl": False,
    "hitl_context": None,
    "last_problem_id": None,
    "input_mode": "Text",
    "ocr_text": "", "ocr_conf": 1.0, "ocr_confirmed": False,
    "asr_text": "", "asr_conf": 1.0, "asr_confirmed": False,
    "img_path": None, "audio_path": None,
    "feedback_given": False,
    "show_fb_input": False,
    "show_correction_input": False,
}
for k, v in _DEFAULTS.items():
    st.session_state.setdefault(k, v)

def _reset():
    for k, v in _DEFAULTS.items():
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _strip_display_delimiters(text: str) -> str:
    """Remove $$ or $ wrappers added for KaTeX display before sending to LLM pipeline."""
    t = text.strip()
    if t.startswith("$$") and t.endswith("$$"):
        return t[2:-2].strip()
    if t.startswith("$") and t.endswith("$") and t.count("$") == 2:
        return t[1:-1].strip()
    return t


def _run_pipeline(text: str, input_type: str = "text"):
    # Strip display-only $$ delimiters before sending to LLM
    clean_text = _strip_display_delimiters(text)
    with st.spinner("⚙️ Running 5-agent pipeline…"):
        state = MathMentorState(extracted_text=clean_text, input_type=input_type, agent_trace=[])
        try:
            result = graph.invoke(state)
            st.session_state.graph_state = dict(result)
            st.session_state.last_problem_id = result.get("last_problem_id")
            st.session_state.feedback_given = False
            st.session_state.show_fb_input = False
            if result.get("needs_hitl"):
                st.session_state.awaiting_hitl = True
                st.session_state.hitl_context = get_hitl_context(dict(result))
            else:
                st.session_state.awaiting_hitl = False
        except Exception as e:
            logger.error("Pipeline error: %s", e)
            st.error(f"Pipeline error: {e}")

def _conf_badge(score: float):
    if score >= 0.8: return f'<span class="conf-g">🟢 {score:.0%}</span>'
    if score >= 0.6: return f'<span class="conf-y">🟡 {score:.0%}</span>'
    return f'<span class="conf-r">🔴 {score:.0%}</span>'

def _agent_badge(agent: str):
    cls = {"Parser":"bp","Intent Router":"br","Solver":"bs","Verifier":"bv","Explainer":"be"}.get(agent,"bp")
    return f'<span class="badge {cls}">{agent}</span>'

import html as _html_lib
import streamlit.components.v1 as components

# ── KaTeX iframe renderer ─────────────────────────────────────────────────────
_KATEX_HEAD = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
"""

def _katex_page(body_html: str, bg="rgba(99,102,241,0.07)",
                border="1px solid rgba(99,102,241,0.25)",
                pad="12px 16px", extra="") -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">{_KATEX_HEAD}
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
/* Auto dark/light — reads OS/browser preference which matches Streamlit theme */
@media(prefers-color-scheme:dark){{
  body{{background:{bg};color:#e8eaf0!important}}
  .step-hdr{{color:#94a3b8!important}}
  .lbl{{color:#818cf8!important}}
  .fin{{background:rgba(22,163,74,.18)!important}}
  .key{{background:rgba(59,130,246,.18)!important}}
}}
@media(prefers-color-scheme:light){{
  body{{background:{bg};color:#1e1e2e!important}}
  .step-hdr{{color:#475569!important}}
}}
body{{font-family:'Segoe UI',system-ui,sans-serif;font-size:15px;line-height:1.9;
     border:{border};border-radius:8px;padding:{pad};
     overflow-x:auto;{extra}}}
.katex-display{{overflow-x:auto;overflow-y:hidden}}
.lbl{{font-size:10px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;
      margin-bottom:5px}}
.step-hdr{{font-size:11px;font-weight:700;letter-spacing:.4px;
           text-transform:uppercase;margin:10px 0 2px}}
.fin{{background:rgba(22,163,74,.12);border-left:3px solid #16A34A;
      border-radius:6px;padding:8px 14px;margin:8px 0;font-weight:600}}
.key{{background:rgba(37,99,235,.10);border-left:3px solid #3B82F6;
      border-radius:6px;padding:8px 14px;margin:8px 0}}
</style></head><body>
{body_html}
<script>
renderMathInElement(document.body,{{
  delimiters:[{{left:"$$",right:"$$",display:true}},
              {{left:"$",right:"$",display:false}}],
  throwOnError:false
}});
</script>
</body></html>"""


def _auto_wrap_latex(text: str) -> str:
    """
    If text has LaTeX commands (\\int, \\frac, ^, _{ etc) but no $ delimiters,
    wrap the whole thing in $$ so KaTeX auto-render fires.
    If text has mixed prose + LaTeX fragments, wrap each LaTeX fragment inline.
    """
    import re as _r
    if not text:
        return text
    # Already has delimiters — leave as-is
    if "$" in text or "\\(" in text or "\\[" in text:
        return text
    # Has LaTeX commands — wrap entire thing as display math
    if _r.search(r'[\\][a-zA-Z]|[\^][{]|[_][{]', text):
        return f"$${text}$$"
    return text


def _render_math_preview(text: str, label: str = "Rendered Preview", height: int = 90):
    """Renders math in a KaTeX iframe — auto-wraps bare LaTeX in $$ delimiters."""
    if not text or not text.strip():
        return
    wrapped = _auto_wrap_latex(text.strip())
    safe = _html_lib.escape(wrapped)
    body = f'<div class="lbl">{label}</div><div>{safe}</div>'
    components.html(_katex_page(body), height=height + 28, scrolling=True)


def _render_answer_box(final: str):
    """Renders the final answer box with KaTeX math."""
    if not final:
        return
    wrapped = _auto_wrap_latex(final.strip())
    safe = _html_lib.escape(wrapped)
    body = f'<div class="lbl">🎯 Final Answer</div><div>{safe}</div>'
    h = min(200, 50 + max(1, final.count("\n") + 1) * 36)
    components.html(
        _katex_page(body, bg="rgba(22,163,74,.09)",
                    border="1px solid rgba(22,163,74,.35)",
                    extra="border-left:4px solid #16A34A"),
        height=h + 28, scrolling=False
    )


def _render_explanation(exp: str, final: str):
    """Render step-by-step explanation using simple st.markdown — reliable, no iframe height issues."""
    if not exp:
        return
    lines = exp.split("\n")
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if ln.startswith("FINAL ANSWER:"):
            st.markdown(f'<div class="final-line">🎯 {ln}</div>', unsafe_allow_html=True)
        elif ln.startswith("KEY CONCEPT:"):
            st.markdown(f'<div class="key-line">💡 {ln}</div>', unsafe_allow_html=True)
        elif ln.startswith("STEP"):
            st.markdown(f'<div class="step-line"><b>{ln}</b></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="step-line">{ln}</div>', unsafe_allow_html=True)


# 2. SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🧠 Math Mentor")
    st.caption("AI-powered JEE Math Solver")
    st.divider()

    mode = st.radio("**Input Mode**", ["Text", "Image", "Audio"],
                    index=["Text","Image","Audio"].index(st.session_state.input_mode),
                    horizontal=True, key="_mode")
    if mode != st.session_state.input_mode:
        _reset()
        st.session_state.input_mode = mode
        st.rerun()

    st.divider()
    st.markdown("**⚙️ Confidence Thresholds**")
    ocr_t = st.slider("OCR", 0.0, 1.0, float(os.getenv("OCR_CONFIDENCE_THRESHOLD","0.75")), 0.05)
    asr_t = st.slider("ASR", 0.0, 1.0, float(os.getenv("ASR_CONFIDENCE_THRESHOLD","0.75")), 0.05)
    ver_t = st.slider("Verifier", 0.0, 1.0, float(os.getenv("VERIFIER_CONFIDENCE_THRESHOLD","0.80")), 0.05)
    os.environ["OCR_CONFIDENCE_THRESHOLD"] = str(ocr_t)
    os.environ["ASR_CONFIDENCE_THRESHOLD"] = str(asr_t)
    os.environ["VERIFIER_CONFIDENCE_THRESHOLD"] = str(ver_t)

    st.divider()
    with st.expander("📖 How it works"):
        st.markdown("""
**5-agent LangGraph pipeline:**

1. 🔍 **Parser** — Extracts structure & variables
2. 🔀 **Router** — Topic classification
3. 🧮 **Solver** — RAG + SymPy + LLaMA 3.3
4. ✅ **Verifier** — Critiques, flags errors
5. 📝 **Explainer** — Student-friendly steps

**HITL triggers:** Low OCR/ASR confidence,
low verifier score

**Math rendering:** KaTeX — use `$...$` for
inline and `$$...$$` for display math.
""")

    st.divider()
    try:
        probs = [p for p in load_all_problems() if p.get("type") == "solved"]
        st.metric("📚 Problems in Memory", len(probs))
    except Exception:
        pass

    if st.button("🔄 New Problem", use_container_width=True):
        _reset()
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 3. MAIN HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("## 🧠 Math Mentor")
st.markdown("*Multimodal JEE Math Solver — Algebra · Probability · Calculus · Linear Algebra*")
st.divider()

left, right = st.columns([1, 1], gap="large")

# ─────────────────────────────────────────────────────────────────────────────
# 4. INPUT PANEL (left column)
# ─────────────────────────────────────────────────────────────────────────────
with left:
    mode = st.session_state.input_mode

    # ── TEXT ──────────────────────────────────────────────────────────────────
    if mode == "Text":
        st.markdown("### ✏️ Enter Problem")
        txt = st.text_area("Problem", height=140, label_visibility="collapsed",
            placeholder="e.g. Solve x^2 - 5x + 6 = 0\ne.g. Differentiate x^3 + 2x w.r.t. x\ne.g. P(AUB) where P(A)=0.3, P(B)=0.5")
        if st.button("🚀 Solve", type="primary", use_container_width=True,
                     disabled=not bool(txt.strip())):
            st.session_state.graph_state = None
            _run_pipeline(txt.strip(), "text")
            st.rerun()

    # ── IMAGE ─────────────────────────────────────────────────────────────────
    elif mode == "Image":
        st.markdown("### 🖼️ Upload Problem Image")
        up_img = st.file_uploader("Image", type=["jpg","jpeg","png"],
                                  label_visibility="collapsed")
        if up_img:
            uploads = os.path.join(_ROOT, "uploads")
            os.makedirs(uploads, exist_ok=True)
            img_path = os.path.join(uploads, f"img_{up_img.name}")
            if st.session_state.img_path != img_path:
                with open(img_path, "wb") as f: f.write(up_img.read())
                st.session_state.img_path = img_path
                st.session_state.ocr_text = ""
                st.session_state.ocr_confirmed = False
                st.session_state.ocr_conf = 1.0

            st.image(img_path, use_container_width=True)

            if not st.session_state.ocr_text:
                with st.spinner("🔍 Extracting text…"):
                    try:
                        from input_processing.image_processor import process_image
                        r = process_image(img_path)
                        st.session_state.ocr_text = r.get("extracted_text","")
                        st.session_state.ocr_conf = r.get("confidence", 1.0)
                        if not st.session_state.ocr_text:
                            st.error("Could not extract text from image.")
                        elif st.session_state.ocr_conf < ocr_t:
                            st.session_state.awaiting_hitl = True
                            st.session_state.hitl_context = {
                                "trigger_type": "ocr",
                                "reason": f"Low OCR confidence ({st.session_state.ocr_conf:.0%}) — please verify.",
                                "current_text": st.session_state.ocr_text,
                                "confidence": st.session_state.ocr_conf,
                            }
                        else:
                            st.session_state.ocr_confirmed = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"OCR failed: {e}")

            if st.session_state.ocr_text:
                c1, c2 = st.columns([3,1])
                c1.markdown("**Extracted math (rendered):**")
                c2.markdown(_conf_badge(st.session_state.ocr_conf), unsafe_allow_html=True)

                # ── Rendered math — what the system understood ─────────────
                _render_math_preview(st.session_state.ocr_text, "🔢 Extracted Math")

                # ── Plain-English correction (no LaTeX needed) ─────────────
                st.caption("✏️ Something wrong? Describe the correction in plain English:")
                ocr_correction = st.text_area(
                    "Plain English correction",
                    placeholder="e.g. The upper limit should be tan(x) not tan(2x)\n"
                                "e.g. The fraction is t dt over 1 plus t squared\n"
                                "e.g. Looks correct — leave blank",
                    height=80, label_visibility="collapsed", key="ocr_correction_box"
                )

                if st.session_state.ocr_confirmed:
                    if st.button("🚀 Solve", type="primary", use_container_width=True):
                        st.session_state.graph_state = None
                        # Combine extracted math + human note for the pipeline
                        final_text = st.session_state.ocr_text
                        if ocr_correction.strip():
                            final_text = (
                                f"{st.session_state.ocr_text}\n"
                                f"[Human note: {ocr_correction.strip()}]"
                            )
                        _run_pipeline(final_text, "image")
                        st.rerun()

    # ── AUDIO ─────────────────────────────────────────────────────────────────
    elif mode == "Audio":
        st.markdown("### 🎙️ Upload Audio Problem")
        up_aud = st.file_uploader("Audio", type=["mp3","wav","m4a","ogg","flac"],
                                  label_visibility="collapsed")
        if up_aud:
            uploads = os.path.join(_ROOT, "uploads")
            os.makedirs(uploads, exist_ok=True)
            aud_path = os.path.join(uploads, f"audio_{up_aud.name}")
            if st.session_state.audio_path != aud_path:
                with open(aud_path, "wb") as f: f.write(up_aud.read())
                st.session_state.audio_path = aud_path
                st.session_state.asr_text = ""
                st.session_state.asr_confirmed = False
                st.session_state.asr_conf = 1.0

            if not st.session_state.asr_text:
                with st.spinner("🎙️ Transcribing…"):
                    try:
                        from input_processing.audio_processor import process_audio
                        r = process_audio(aud_path)
                        st.session_state.asr_text = r.get("extracted_text","")
                        st.session_state.asr_conf = r.get("confidence", 1.0)
                        if not st.session_state.asr_text:
                            st.error("No transcript returned. Check the audio file.")
                        elif st.session_state.asr_conf < asr_t:
                            st.session_state.awaiting_hitl = True
                            st.session_state.hitl_context = {
                                "trigger_type": "asr",
                                "reason": f"Low ASR confidence ({st.session_state.asr_conf:.0%}) — please verify.",
                                "current_text": st.session_state.asr_text,
                                "confidence": st.session_state.asr_conf,
                            }
                        else:
                            st.session_state.asr_confirmed = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"ASR failed: {e}")

            if st.session_state.asr_text:
                c1, c2 = st.columns([3,1])
                c1.markdown("**Transcript (rendered):**")
                c2.markdown(_conf_badge(st.session_state.asr_conf), unsafe_allow_html=True)

                # ── Rendered math ──────────────────────────────────────────
                _render_math_preview(st.session_state.asr_text, "🔢 Transcribed Math")

                # ── Plain-English correction ───────────────────────────────
                st.caption("✏️ Something wrong? Describe the correction in plain English:")
                asr_correction = st.text_area(
                    "Plain English correction",
                    placeholder="e.g. It said x cubed but should be x squared\n"
                                "e.g. The integral goes from 0 to pi, not 0 to 1\n"
                                "e.g. Looks correct — leave blank",
                    height=80, label_visibility="collapsed", key="asr_correction_box"
                )
                if st.session_state.asr_confirmed:
                    if st.button("🚀 Solve", type="primary", use_container_width=True):
                        st.session_state.graph_state = None
                        final_text = st.session_state.asr_text
                        if asr_correction.strip():
                            final_text = (
                                f"{st.session_state.asr_text}\n"
                                f"[Human note: {asr_correction.strip()}]"
                            )
                        _run_pipeline(final_text, "audio")
                        st.rerun()

    # ─────────────────────────────────────────────────────────────────────────
    # 5. HITL PANEL
    # ─────────────────────────────────────────────────────────────────────────
    if st.session_state.awaiting_hitl and st.session_state.hitl_context:
        ctx = st.session_state.hitl_context
        ttype = ctx.get("trigger_type","")
        st.divider()

        if ttype in ("ocr","asr"):
            st.warning(f"⚠️ **Review Needed** — {ctx.get('reason','')}")

            # Rendered math — shown for human to visually confirm
            _render_math_preview(ctx.get("current_text",""), "🔢 Rendered Math — is this correct?")

            st.caption("✏️ Something wrong? Describe the correction in plain English (leave blank if correct):")
            edited = st.text_area(
                "Plain English correction",
                placeholder="e.g. The upper limit should be cot(x) not cos(x)\n"
                            "e.g. The denominator is t times (1 + t squared)\n"
                            "e.g. Looks correct — leave blank and click ✅",
                height=80, key="hitl_edit_area"
            )

            h1, h2, h3 = st.columns(3)
            with h1:
                if st.button("✅ Looks correct", use_container_width=True, type="primary"):
                    st.session_state.awaiting_hitl = False
                    if ttype == "ocr": st.session_state.ocr_confirmed = True
                    else:              st.session_state.asr_confirmed = True
                    st.rerun()
            with h2:
                if st.button("✏️ Apply correction", use_container_width=True):
                    st.session_state.awaiting_hitl = False
                    # edited is now plain English — append as a human note
                    base = ctx.get("current_text", "")
                    corrected = f"{base}\n[Human note: {edited.strip()}]" if edited.strip() else base
                    if ttype == "ocr":
                        st.session_state.ocr_text = corrected
                        st.session_state.ocr_confirmed = True
                    else:
                        st.session_state.asr_text = corrected
                        st.session_state.asr_confirmed = True
                    st.rerun()
            with h3:
                if st.button("❌ Start over", use_container_width=True):
                    _reset()
                    st.rerun()

        elif ttype == "verifier":
            gs = st.session_state.graph_state or {}
            st.error(
                f"🔴 **Verifier flagged this solution** "
                f"(score: {gs.get('verifier_score',0):.0%})\n\n"
                f"{gs.get('verifier_notes','')}"
            )
            with st.expander("👁️ View flagged solution", expanded=True):
                solver_out = gs.get("solver_output","")
                st.markdown(
                    f'<div style="max-height:300px;overflow-y:auto;overflow-x:auto;'
                    f'background:rgba(0,0,0,0.04);border:1px solid rgba(148,163,184,0.3);'
                    f'border-radius:8px;padding:12px 16px;font-family:monospace;'
                    f'font-size:13px;line-height:1.7;white-space:pre-wrap;color:inherit">'
                    f'{solver_out}</div>',
                    unsafe_allow_html=True
                )

            h1, h2, h3 = st.columns(3)
            with h1:
                if st.button("✅ Correct as-is", use_container_width=True, type="primary"):
                    updated = apply_human_decision(dict(gs), "approve")
                    with st.spinner("📝 Generating explanation…"):
                        from agents.explainer_agent import explainer_node
                        final = explainer_node(updated)
                        st.session_state.graph_state = dict(final)
                        st.session_state.last_problem_id = final.get("last_problem_id")
                    st.session_state.awaiting_hitl = False
                    st.rerun()
            with h2:
                if st.button("📝 Submit correction", use_container_width=True):
                    st.session_state.show_correction_input = True
                    st.rerun()
            with h3:
                if st.button("🔄 Re-solve", use_container_width=True):
                    st.session_state.awaiting_hitl = False
                    _run_pipeline(gs.get("extracted_text",""), gs.get("input_type","text"))
                    st.rerun()

            if st.session_state.show_correction_input:
                corr = st.text_area("Provide the correct solution (LaTeX OK):", height=110, key="corr_text")
                if corr.strip():
                    _render_math_preview(corr, "Preview your correction")
                if st.button("✔️ Submit correction", type="primary"):
                    updated = apply_human_decision(dict(gs), "edit", edited_text=corr)
                    with st.spinner("📝 Generating explanation…"):
                        from agents.explainer_agent import explainer_node
                        final = explainer_node(updated)
                        st.session_state.graph_state = dict(final)
                        st.session_state.last_problem_id = final.get("last_problem_id")
                    st.session_state.awaiting_hitl = False
                    st.session_state.show_correction_input = False
                    st.rerun()

        else:
            # ── Parser / general HITL — problem needs clarification ────────────
            gs = st.session_state.graph_state or {}
            reason = ctx.get("reason", gs.get("hitl_reason", "The problem needs clarification."))
            st.warning(f"⚠️ **Clarification Needed** — {reason}")

            # Show what was extracted
            extracted = gs.get("extracted_text", ctx.get("current_text",""))
            if extracted:
                _render_math_preview(extracted, "🔢 What was extracted — is this the right problem?")

            st.caption("✏️ Describe in plain English what the problem actually is:")
            clarification = st.text_area(
                "Clarification",
                placeholder=(
                    "e.g. The expression is a fraction: the numerator is (5050) times integral from 0 to 1 of (1-x^50)^100 dx\n"
                    "e.g. and the denominator is integral from 0 to 1 of (1-x^50)^101 dx\n"
                    "e.g. Find the value of this fraction"
                ),
                height=110, key="parser_clarification"
            )

            h1, h2 = st.columns(2)
            with h1:
                if st.button("🚀 Solve with clarification", type="primary", use_container_width=True,
                             disabled=not clarification.strip()):
                    # Re-run pipeline with original text + human clarification merged
                    base = extracted or ""
                    clarified_text = f"{base}\n[Human clarification: {clarification.strip()}]"
                    st.session_state.awaiting_hitl = False
                    st.session_state.graph_state = None
                    _run_pipeline(clarified_text, gs.get("input_type","text"))
                    st.rerun()
            with h2:
                if st.button("❌ Start over", use_container_width=True):
                    _reset()
                    st.rerun()

    # ─────────────────────────────────────────────────────────────────────────
    # 6. AGENT TRACE + CONTEXT EXPANDERS
    # ─────────────────────────────────────────────────────────────────────────
    gs = st.session_state.graph_state
    if gs:
        trace = gs.get("agent_trace", [])
        if trace:
            st.divider()
            with st.expander(f"🔍 Agent Trace ({len(trace)} agents)", expanded=False):
                for entry in trace:
                    ag  = entry.get("agent","?")
                    act = entry.get("action","")
                    out = entry.get("output","")
                    st.markdown(
                        f'{_agent_badge(ag)} <code style="font-size:11px">{act}</code>',
                        unsafe_allow_html=True
                    )
                    if out:
                        st.caption(out)
                route = gs.get("workflow_route","")
                if route:
                    r_map = {"solve":"🟢 solve","reject":"🔴 reject",
                             "hitl":"🟡 hitl","clarify":"🔵 clarify","error":"⛔ error"}
                    st.markdown(f"**Route:** `{r_map.get(route, route)}`")

        ctx_chunks = gs.get("retrieved_context", [])
        with st.expander(f"📚 Retrieved Context ({len(ctx_chunks)} chunks)", expanded=False):
            if ctx_chunks:
                for chunk in ctx_chunks:
                    rel = float(chunk.get("relevance", 0))
                    src = chunk.get("source","unknown")
                    txt = chunk.get("content","")
                    st.markdown(f"**📄 {src}** — {rel:.0%}")
                    st.progress(min(rel, 1.0))
                    st.code(txt[:280]+("…" if len(txt)>280 else ""), language="text")
                    st.markdown("---")
            else:
                st.info("No context retrieved — solved from LLM knowledge.")

# ─────────────────────────────────────────────────────────────────────────────
# 7. RESULTS PANEL (right column)
# ─────────────────────────────────────────────────────────────────────────────
with right:
    gs = st.session_state.graph_state

    # ── Empty state ───────────────────────────────────────────────────────────
    if gs is None and not st.session_state.awaiting_hitl:
        st.markdown("### 📋 Solution appears here")
        st.markdown("""
| Topic | Examples |
|-------|---------|
| 📐 Algebra | Quadratics, polynomials, systems |
| 📊 Probability | Events, distributions |
| 📈 Calculus | Derivatives, integrals, limits |
| 🔢 Linear Algebra | Matrices, determinants |
""")
        st.info("Select an input mode on the left and submit a problem.")

    # ── HITL waiting ──────────────────────────────────────────────────────────
    elif st.session_state.awaiting_hitl and not (gs and gs.get("final_answer")):
        st.markdown("### ⏳ Awaiting Human Review")
        st.info("Respond to the review panel on the left to continue.")

    # ── Rejected / error ──────────────────────────────────────────────────────
    elif gs and gs.get("workflow_route") in ("reject","error","clarify"):
        route = gs.get("workflow_route","")
        st.markdown("### ℹ️ Result")
        if route == "reject":
            st.info("This doesn't appear to be a JEE math problem. "
                    "Try algebra, calculus, probability, or linear algebra.")
        elif route == "clarify":
            st.warning("The problem needs clarification. Please rephrase and try again.")
        else:
            st.error(f"Pipeline error: {gs.get('error','Unknown error')}")

    # ── Full solution ──────────────────────────────────────────────────────────
    elif gs and (gs.get("final_answer") or gs.get("explanation")):
        score = float(gs.get("verifier_score") or 0)
        final = gs.get("final_answer","")
        exp   = gs.get("explanation","")

        is_good = score >= ver_t
        header  = "✅ Solution" if is_good else "⚠️ Solution (Needs Review)"
        st.markdown(f"### {header}")

        # Confidence row
        st.markdown(_conf_badge(score) + " confidence", unsafe_allow_html=True)
        st.progress(min(score, 1.0))
        if gs.get("verifier_notes") and not is_good:
            st.caption(f"Issues: {gs['verifier_notes']}")

        # ── Final answer box with KaTeX rendering ─────────────────────────
        if final:
            _render_answer_box(final)

        # SymPy check
        sym = gs.get("sympy_result","")
        if sym and sym not in ("","Not available"):
            st.caption(f"🔢 SymPy verification: `{sym}`")

        # Memory reuse note
        mem = gs.get("memory_context",[])
        if mem:
            st.caption(f"🧠 {len(mem)} similar past problem(s) injected into solver.")

        st.divider()

        # ── Step-by-step with KaTeX rendering ─────────────────────────────
        if exp:
            st.markdown("**Step-by-step Explanation:**")
            _render_explanation(exp, final)

        st.divider()

        # ── Feedback ──────────────────────────────────────────────────────
        pid = st.session_state.last_problem_id
        if not st.session_state.feedback_given:
            st.markdown("**Was this helpful?**")
            fb1, fb2 = st.columns(2)
            with fb1:
                if st.button("✅ Correct", use_container_width=True):
                    if pid:
                        try: save_feedback(pid, "correct")
                        except Exception: pass
                    st.session_state.feedback_given = True
                    st.rerun()
            with fb2:
                if st.button("❌ Incorrect", use_container_width=True):
                    st.session_state.show_fb_input = True
                    st.rerun()

            if st.session_state.show_fb_input:
                comment = st.text_input("What was wrong? (optional)",
                    placeholder="e.g. Wrong sign in step 2", key="fb_comment")
                if st.button("Submit", type="primary"):
                    if pid:
                        try: save_feedback(pid, "incorrect", comment)
                        except Exception: pass
                    st.session_state.feedback_given = True
                    st.session_state.show_fb_input = False
                    st.rerun()
        else:
            st.success("✅ Feedback saved — thank you!")

    elif gs and gs.get("needs_hitl"):
        st.markdown("### ⏳ Awaiting Human Review")
        st.info("Respond in the left panel to continue.")