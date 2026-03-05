import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title=os.getenv("APP_TITLE", "Math Mentor"), page_icon="🧠")
st.title("🧠 Math Mentor")
st.caption("Phase 1 complete — UI coming in Phase 3")
st.success("✅ Phase 1 Core Pipeline is ready. Parser + Router + RAG are operational.")