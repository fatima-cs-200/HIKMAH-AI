"""
HIKMAH AI — Streamlit Frontend
Dark luxury Islamic-tech interface.
"""

import sys
from pathlib import Path

# Add project root to sys.path so `from utils.config import ...` works
# whether Streamlit is launched via `start_frontend.py` or directly.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import json
import time
from datetime import datetime
from typing import Optional
import streamlit as st
import requests

# ── Page config (must be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="HIKMAH AI",
    page_icon="☪️",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = "http://localhost:8000/api/v1"

# ── CSS Styling ──────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:wght@300;400;500;600&family=Amiri:ital,wght@0,400;0,700;1,400&display=swap');

/* ── Root Variables ── */
:root {
    --navy:   #0B1426;
    --navy2:  #0D1B35;
    --navy3:  #112040;
    --emerald:#0F766E;
    --emerald2:#0D9488;
    --gold:   #D4AF37;
    --gold2:  #F0D060;
    --white:  #F0F4FF;
    --muted:  #8899BB;
    --card:   #0F1E3A;
    --border: #1E3A5F;
    --radius: 16px;
}

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: var(--navy) !important;
    color: var(--white) !important;
}

.stApp { background-color: var(--navy) !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--navy2) 0%, var(--navy3) 100%) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--white) !important; }

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--white) !important;
    font-family: 'Inter', sans-serif !important;
    padding: 12px 16px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--emerald) !important;
    box-shadow: 0 0 0 2px rgba(15,118,110,0.3) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, var(--emerald) 0%, var(--emerald2) 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    padding: 10px 24px !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(15,118,110,0.4) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--white) !important;
}

/* ── Slider ── */
.stSlider > div > div > div > div { background: var(--emerald) !important; }

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 16px !important;
}
[data-testid="metric-container"] label { color: var(--muted) !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--gold) !important;
    font-weight: 700 !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--navy); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--emerald); }
</style>
""", unsafe_allow_html=True)

# ── Component HTML helpers ────────────────────────────────────────────────────

def hero_header():
    st.markdown("""
<div style="text-align:center; padding: 32px 0 24px 0;">
  <div style="font-size:48px; margin-bottom:8px;">☪️</div>
  <h1 style="font-family:'Cinzel',serif; font-size:2.8rem; font-weight:700;
             background:linear-gradient(135deg,#D4AF37,#F0D060);
             -webkit-background-clip:text; -webkit-text-fill-color:transparent;
             margin:0; letter-spacing:4px;">HIKMAH AI</h1>
  <p style="color:#8899BB; font-size:1rem; margin-top:8px; letter-spacing:2px;
            font-family:'Inter',sans-serif; font-weight:300;">
    AUTHENTIC ISLAMIC KNOWLEDGE · QURAN & SAHIH BUKHARI
  </p>
  <div style="width:80px; height:2px;
              background:linear-gradient(90deg,transparent,#D4AF37,transparent);
              margin:16px auto 0;"></div>
</div>
""", unsafe_allow_html=True)


def chat_bubble_user(text: str):
    st.markdown(f"""
<div style="display:flex; justify-content:flex-end; margin:12px 0;">
  <div style="background:linear-gradient(135deg,#0F766E,#0D9488);
              border-radius:18px 18px 4px 18px; padding:14px 18px;
              max-width:75%; box-shadow:0 4px 15px rgba(15,118,110,0.3);">
    <p style="margin:0; color:white; font-size:0.95rem; line-height:1.6;">{text}</p>
  </div>
</div>
""", unsafe_allow_html=True)


def chat_bubble_ai(text: str, sources: list = None):
    sources_html = ""
    if sources:
        badges = ""
        for s in sources[:3]:
            color = "#D4AF37" if s.get("source") == "quran" else "#0F766E"
            badges += f'<span style="background:{color}22; color:{color}; border:1px solid {color}44; border-radius:20px; padding:3px 10px; font-size:0.75rem; margin-right:6px;">{s.get("citation","")}</span>'
        sources_html = f'<div style="margin-top:12px; padding-top:10px; border-top:1px solid #1E3A5F;">{badges}</div>'

    st.markdown(f"""
<div style="display:flex; justify-content:flex-start; margin:12px 0;">
  <div style="background:#0F1E3A; border:1px solid #1E3A5F;
              border-radius:18px 18px 18px 4px; padding:16px 20px;
              max-width:85%; box-shadow:0 4px 20px rgba(0,0,0,0.3);">
    <div style="display:flex; align-items:center; margin-bottom:10px;">
      <span style="font-size:18px; margin-right:8px;">☪️</span>
      <span style="color:#D4AF37; font-size:0.8rem; font-weight:600; letter-spacing:1px;">HIKMAH AI</span>
    </div>
    <p style="margin:0; color:#F0F4FF; font-size:0.95rem; line-height:1.7; white-space:pre-wrap;">{text}</p>
    {sources_html}
  </div>
</div>
""", unsafe_allow_html=True)


def source_card(source: dict, index: int):
    is_quran = source.get("source") == "quran"
    icon = "📖" if is_quran else "📜"
    color = "#D4AF37" if is_quran else "#0F766E"
    meta = source.get("metadata", {})
    confidence = source.get("confidence", 0)

    detail_html = ""
    if is_quran:
        arabic = meta.get("arabic", "")
        english = meta.get("english", "")
        if arabic:
            detail_html += f'<p style="font-family:Amiri,serif; font-size:1.1rem; color:#F0D060; text-align:right; direction:rtl; margin:8px 0;">{arabic}</p>'
        if english:
            detail_html += f'<p style="color:#C0D0E8; font-size:0.88rem; font-style:italic; margin:4px 0;">"{english}"</p>'
    else:
        narrator = meta.get("narrator", "")
        text = meta.get("text", "")
        if narrator:
            detail_html += f'<p style="color:#8899BB; font-size:0.8rem; margin:4px 0;">Narrated by: <span style="color:#D4AF37;">{narrator}</span></p>'
        if text:
            detail_html += f'<p style="color:#C0D0E8; font-size:0.88rem; font-style:italic; margin:4px 0;">"{text[:200]}{"..." if len(text)>200 else ""}"</p>'

    st.markdown(f"""
<div style="background:#0F1E3A; border:1px solid {color}44; border-radius:12px;
            padding:16px; margin:8px 0; border-left:3px solid {color};">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
    <span style="color:{color}; font-weight:600; font-size:0.9rem;">{icon} {source.get('citation','')}</span>
    <span style="background:{color}22; color:{color}; border-radius:20px;
                 padding:2px 10px; font-size:0.75rem; font-weight:600;">
      {confidence}% match
    </span>
  </div>
  {detail_html}
</div>
""", unsafe_allow_html=True)

# ── API helpers ───────────────────────────────────────────────────────────────

def api_health():
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def api_query(question: str, top_k: int, source_filter: Optional[str]) -> Optional[dict]:
    try:
        payload = {"question": question, "top_k": top_k, "source_filter": source_filter}
        r = requests.post(f"{API_BASE}/query", json=payload, timeout=120)
        if r.status_code == 200:
            return r.json()
        st.error(f"API error {r.status_code}: {r.text}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to HIKMAH AI backend. Is the FastAPI server running?")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


def api_search(query: str, source: str, top_k: int) -> Optional[dict]:
    try:
        payload = {"query": query, "source": source, "top_k": top_k}
        r = requests.post(f"{API_BASE}/search", json=payload, timeout=30)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


# ── Session state init ────────────────────────────────────────────────────────

def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "search_history" not in st.session_state:
        st.session_state.search_history = []
    if "active_page" not in st.session_state:
        st.session_state.active_page = "Chat"
    if "health" not in st.session_state:
        st.session_state.health = None
    if "last_health_check" not in st.session_state:
        st.session_state.last_health_check = 0

# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        # Logo
        st.markdown("""
<div style="text-align:center; padding:20px 0 16px;">
  <div style="font-size:36px;">☪️</div>
  <h2 style="font-family:'Cinzel',serif; color:#D4AF37; margin:4px 0; font-size:1.4rem;">HIKMAH AI</h2>
  <p style="color:#8899BB; font-size:0.75rem; letter-spacing:2px; margin:0;">ISLAMIC KNOWLEDGE</p>
</div>
<hr style="border-color:#1E3A5F; margin:0 0 16px;">
""", unsafe_allow_html=True)

        # Navigation
        st.markdown('<p style="color:#8899BB; font-size:0.75rem; letter-spacing:2px; margin-bottom:8px;">NAVIGATION</p>', unsafe_allow_html=True)
        pages = {"💬 Chat": "Chat", "🔍 Search": "Search", "📊 Dashboard": "Dashboard"}
        for label, page in pages.items():
            active = st.session_state.active_page == page
            btn_style = "background:linear-gradient(135deg,#0F766E,#0D9488);" if active else "background:#0F1E3A;"
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.session_state.active_page = page
                st.rerun()

        st.markdown("<hr style='border-color:#1E3A5F;'>", unsafe_allow_html=True)

        # Settings
        st.markdown('<p style="color:#8899BB; font-size:0.75rem; letter-spacing:2px; margin-bottom:8px;">SETTINGS</p>', unsafe_allow_html=True)
        top_k = st.slider("Sources to retrieve", 1, 15, 5, key="top_k")
        source_filter = st.selectbox(
            "Knowledge source",
            ["All Sources", "Quran Only", "Hadith Only"],
            key="source_filter",
        )
        source_map = {"All Sources": None, "Quran Only": "quran", "Hadith Only": "hadith"}

        st.markdown("<hr style='border-color:#1E3A5F;'>", unsafe_allow_html=True)

        # System status
        now = time.time()
        if now - st.session_state.last_health_check > 30:
            st.session_state.health = api_health()
            st.session_state.last_health_check = now

        health = st.session_state.health
        if health:
            status_color = "#0F766E" if health.get("status") == "healthy" else "#F59E0B"
            ollama_color = "#0F766E" if health.get("ollama_connected") else "#EF4444"
            st.markdown(f"""
<div style="background:#0F1E3A; border:1px solid #1E3A5F; border-radius:12px; padding:14px;">
  <p style="color:#8899BB; font-size:0.75rem; letter-spacing:1px; margin:0 0 10px;">SYSTEM STATUS</p>
  <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
    <span style="color:#8899BB; font-size:0.8rem;">API</span>
    <span style="color:{status_color}; font-size:0.8rem; font-weight:600;">● {health.get('status','unknown').upper()}</span>
  </div>
  <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
    <span style="color:#8899BB; font-size:0.8rem;">Ollama</span>
    <span style="color:{ollama_color}; font-size:0.8rem; font-weight:600;">{'● CONNECTED' if health.get('ollama_connected') else '● OFFLINE'}</span>
  </div>
  <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
    <span style="color:#8899BB; font-size:0.8rem;">Quran</span>
    <span style="color:#D4AF37; font-size:0.8rem; font-weight:600;">{health.get('quran_verses',0):,} verses</span>
  </div>
  <div style="display:flex; justify-content:space-between;">
    <span style="color:#8899BB; font-size:0.8rem;">Hadith</span>
    <span style="color:#D4AF37; font-size:0.8rem; font-weight:600;">{health.get('hadith_count',0):,} records</span>
  </div>
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown("""
<div style="background:#1A0A0A; border:1px solid #5F1E1E; border-radius:12px; padding:14px;">
  <p style="color:#EF4444; font-size:0.85rem; margin:0;">⚠️ Backend offline<br><span style="color:#8899BB; font-size:0.75rem;">Start the FastAPI server</span></p>
</div>
""", unsafe_allow_html=True)

        # Search history
        if st.session_state.search_history:
            st.markdown("<hr style='border-color:#1E3A5F;'>", unsafe_allow_html=True)
            st.markdown('<p style="color:#8899BB; font-size:0.75rem; letter-spacing:2px; margin-bottom:8px;">RECENT SEARCHES</p>', unsafe_allow_html=True)
            for item in st.session_state.search_history[-5:][::-1]:
                if st.button(f"↩ {item[:35]}…" if len(item) > 35 else f"↩ {item}", key=f"hist_{item[:20]}", use_container_width=True):
                    st.session_state.prefill_question = item
                    st.session_state.active_page = "Chat"
                    st.rerun()

        # Clear chat
        if st.session_state.messages:
            st.markdown("<hr style='border-color:#1E3A5F;'>", unsafe_allow_html=True)
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

        # Export
        if st.session_state.messages:
            export_data = json.dumps(st.session_state.messages, indent=2, ensure_ascii=False)
            st.download_button(
                "📥 Export Chat",
                data=export_data,
                file_name=f"hikmah_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True,
            )

    return top_k, source_map[source_filter]

# ── Chat Page ─────────────────────────────────────────────────────────────────

def render_chat_page(top_k: int, source_filter: Optional[str]):
    hero_header()

    # Suggested questions
    if not st.session_state.messages:
        st.markdown("""
<div style="text-align:center; margin-bottom:24px;">
  <p style="color:#8899BB; font-size:0.85rem; letter-spacing:1px;">ASK ABOUT ISLAM</p>
</div>
""", unsafe_allow_html=True)
        suggestions = [
            "What does the Quran say about patience?",
            "What are the five pillars of Islam?",
            "What does Islam say about kindness to parents?",
            "What is the virtue of fasting in Ramadan?",
        ]
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                    st.session_state.prefill_question = suggestion
                    st.rerun()

    # Chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                chat_bubble_user(msg["content"])
            else:
                chat_bubble_ai(msg["content"], msg.get("sources", []))
                if msg.get("sources"):
                    with st.expander(f"📚 View {len(msg['sources'])} source(s)", expanded=False):
                        for i, src in enumerate(msg["sources"]):
                            source_card(src, i)

    # Input area
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    prefill = st.session_state.pop("prefill_question", "")
    col1, col2 = st.columns([5, 1])
    with col1:
        question = st.text_input(
            "Ask your question",
            value=prefill,
            placeholder="e.g. What does Islam say about seeking knowledge?",
            label_visibility="collapsed",
            key="chat_input",
        )
    with col2:
        ask_btn = st.button("Ask ✦", use_container_width=True, key="ask_btn")

    if (ask_btn or question) and question.strip():
        if ask_btn or (question != prefill and question.strip()):
            _handle_chat_query(question.strip(), top_k, source_filter)


def _handle_chat_query(question: str, top_k: int, source_filter: Optional[str]):
    # Add to history
    if question not in st.session_state.search_history:
        st.session_state.search_history.append(question)

    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})
    chat_bubble_user(question)

    # Typing animation + API call
    with st.spinner(""):
        st.markdown("""
<div style="display:flex; align-items:center; gap:8px; padding:12px 0;">
  <span style="color:#D4AF37; font-size:18px;">☪️</span>
  <span style="color:#8899BB; font-size:0.9rem; font-style:italic;">Searching Islamic sources…</span>
</div>
""", unsafe_allow_html=True)
        result = api_query(question, top_k, source_filter)

    if result:
        answer = result.get("answer", "No answer returned.")
        sources = result.get("sources", [])
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
        })
        chat_bubble_ai(answer, sources)
        if sources:
            with st.expander(f"📚 View {len(sources)} source(s)", expanded=True):
                for i, src in enumerate(sources):
                    source_card(src, i)

        # Copy button
        st.markdown(f"""
<div style="display:flex; gap:8px; margin-top:8px;">
  <button onclick="navigator.clipboard.writeText({json.dumps(answer)})"
          style="background:#0F1E3A; border:1px solid #1E3A5F; color:#8899BB;
                 border-radius:8px; padding:6px 14px; cursor:pointer; font-size:0.8rem;">
    📋 Copy Answer
  </button>
</div>
""", unsafe_allow_html=True)
    st.rerun()

# ── Search Page ───────────────────────────────────────────────────────────────

def render_search_page():
    st.markdown("""
<div style="padding:24px 0 16px;">
  <h2 style="font-family:'Cinzel',serif; color:#D4AF37; margin:0;">🔍 Semantic Search</h2>
  <p style="color:#8899BB; font-size:0.9rem; margin-top:4px;">Search directly across Quran verses and Hadith</p>
</div>
""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([4, 2, 1])
    with col1:
        query = st.text_input("Search query", placeholder="e.g. mercy, prayer, patience", label_visibility="collapsed")
    with col2:
        source = st.selectbox("Source", ["all", "quran", "hadith"], label_visibility="collapsed")
    with col3:
        search_btn = st.button("Search", use_container_width=True)

    if search_btn and query.strip():
        with st.spinner("Searching…"):
            result = api_search(query.strip(), source, 10)

        if result and result.get("results"):
            results = result["results"]
            st.markdown(f"""
<div style="margin:16px 0 8px;">
  <span style="color:#D4AF37; font-weight:600;">{len(results)}</span>
  <span style="color:#8899BB;"> results for "</span>
  <span style="color:#F0F4FF;">{query}</span>
  <span style="color:#8899BB;">"</span>
</div>
""", unsafe_allow_html=True)

            for r in results:
                is_quran = r.get("source") == "quran"
                icon = "📖" if is_quran else "📜"
                color = "#D4AF37" if is_quran else "#0F766E"
                meta = r.get("metadata", {})
                confidence = r.get("confidence", 0)

                arabic_html = ""
                if is_quran and meta.get("arabic"):
                    arabic_html = f'<p style="font-family:Amiri,serif; font-size:1.1rem; color:#F0D060; text-align:right; direction:rtl; margin:8px 0 4px;">{meta["arabic"]}</p>'

                body_text = meta.get("english", "") if is_quran else meta.get("text", "")
                narrator_html = ""
                if not is_quran and meta.get("narrator"):
                    narrator_html = f'<p style="color:#8899BB; font-size:0.8rem; margin:4px 0;">Narrated by: <span style="color:#D4AF37;">{meta["narrator"]}</span></p>'

                st.markdown(f"""
<div style="background:#0F1E3A; border:1px solid {color}33; border-radius:14px;
            padding:18px; margin:10px 0; border-left:3px solid {color};">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
    <span style="color:{color}; font-weight:600;">{icon} {r.get('citation','')}</span>
    <span style="background:{color}22; color:{color}; border-radius:20px; padding:2px 10px; font-size:0.75rem;">{confidence}% match</span>
  </div>
  {arabic_html}
  {narrator_html}
  <p style="color:#C0D0E8; font-size:0.9rem; line-height:1.6; margin:0; font-style:italic;">"{body_text}"</p>
</div>
""", unsafe_allow_html=True)
        elif result:
            st.markdown("""
<div style="text-align:center; padding:40px; color:#8899BB;">
  <div style="font-size:40px; margin-bottom:12px;">🔍</div>
  <p>No results found. Try a different search term.</p>
</div>
""", unsafe_allow_html=True)

# ── Dashboard Page ────────────────────────────────────────────────────────────

def render_dashboard_page():
    st.markdown("""
<div style="padding:24px 0 16px;">
  <h2 style="font-family:'Cinzel',serif; color:#D4AF37; margin:0;">📊 Dashboard</h2>
  <p style="color:#8899BB; font-size:0.9rem; margin-top:4px;">System overview and knowledge base statistics</p>
</div>
""", unsafe_allow_html=True)

    health = api_health()
    if not health:
        st.error("Backend is offline. Start the FastAPI server to view stats.")
        return

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Quran Verses", f"{health.get('quran_verses', 0):,}")
    with col2:
        st.metric("Hadith Records", f"{health.get('hadith_count', 0):,}")
    with col3:
        st.metric("LLM Model", health.get("version", "—"))
    with col4:
        status = "🟢 Healthy" if health.get("status") == "healthy" else "🟡 Degraded"
        st.metric("API Status", status)

    st.markdown("<hr style='border-color:#1E3A5F; margin:24px 0;'>", unsafe_allow_html=True)

    # Info cards
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
<div style="background:#0F1E3A; border:1px solid #1E3A5F; border-radius:14px; padding:20px;">
  <h3 style="color:#D4AF37; font-family:'Cinzel',serif; margin:0 0 16px; font-size:1rem;">📖 Quran Collection</h3>
  <p style="color:#8899BB; font-size:0.85rem; line-height:1.7; margin:0;">
    The Noble Quran — 114 Surahs, 6,236 Ayat.<br>
    Stored with Arabic text, English translation (Sahih International),
    Surah name, and verse number metadata.<br><br>
    Embedding model: <span style="color:#D4AF37;">BAAI/bge-base-en-v1.5</span><br>
    Vector store: <span style="color:#0F766E;">ChromaDB (cosine similarity)</span>
  </p>
</div>
""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
<div style="background:#0F1E3A; border:1px solid #1E3A5F; border-radius:14px; padding:20px;">
  <h3 style="color:#D4AF37; font-family:'Cinzel',serif; margin:0 0 16px; font-size:1rem;">📜 Sahih Bukhari Collection</h3>
  <p style="color:#8899BB; font-size:0.85rem; line-height:1.7; margin:0;">
    Sahih al-Bukhari — the most authentic hadith collection.<br>
    Stored with book name, chapter, hadith number, narrator,
    and full English text.<br><br>
    Compiled by: <span style="color:#D4AF37;">Imam Muhammad al-Bukhari</span><br>
    Grading: <span style="color:#0F766E;">Sahih (Authentic)</span>
  </p>
</div>
""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Architecture card
    st.markdown("""
<div style="background:#0F1E3A; border:1px solid #1E3A5F; border-radius:14px; padding:20px;">
  <h3 style="color:#D4AF37; font-family:'Cinzel',serif; margin:0 0 16px; font-size:1rem;">⚙️ RAG Architecture</h3>
  <div style="display:flex; gap:12px; flex-wrap:wrap;">
    <span style="background:#0F766E22; color:#0F766E; border:1px solid #0F766E44; border-radius:20px; padding:6px 14px; font-size:0.8rem;">🔤 BAAI/bge-base-en-v1.5</span>
    <span style="background:#D4AF3722; color:#D4AF37; border:1px solid #D4AF3744; border-radius:20px; padding:6px 14px; font-size:0.8rem;">🗄️ ChromaDB</span>
    <span style="background:#0F766E22; color:#0F766E; border:1px solid #0F766E44; border-radius:20px; padding:6px 14px; font-size:0.8rem;">🦙 Llama 3 via Ollama</span>
    <span style="background:#D4AF3722; color:#D4AF37; border:1px solid #D4AF3744; border-radius:20px; padding:6px 14px; font-size:0.8rem;">⚡ FastAPI</span>
    <span style="background:#0F766E22; color:#0F766E; border:1px solid #0F766E44; border-radius:20px; padding:6px 14px; font-size:0.8rem;">🎨 Streamlit</span>
    <span style="background:#D4AF3722; color:#D4AF37; border:1px solid #D4AF3744; border-radius:20px; padding:6px 14px; font-size:0.8rem;">🔗 LangChain</span>
  </div>
</div>
""", unsafe_allow_html=True)

    # Chat stats
    if st.session_state.messages:
        st.markdown("<hr style='border-color:#1E3A5F; margin:24px 0;'>", unsafe_allow_html=True)
        user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
        ai_msgs = [m for m in st.session_state.messages if m["role"] == "assistant"]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Questions Asked", len(user_msgs))
        with col2:
            st.metric("Answers Given", len(ai_msgs))
        with col3:
            total_sources = sum(len(m.get("sources", [])) for m in ai_msgs)
            st.metric("Sources Cited", total_sources)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    inject_css()
    init_session()
    top_k, source_filter = render_sidebar()

    page = st.session_state.active_page
    if page == "Chat":
        render_chat_page(top_k, source_filter)
    elif page == "Search":
        render_search_page()
    elif page == "Dashboard":
        render_dashboard_page()


if __name__ == "__main__":
    main()
