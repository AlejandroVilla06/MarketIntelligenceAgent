"""
Market Intelligence Agent — Streamlit Dashboard
================================================

Futuristic 2028 chat interface with glassmorphism, ambient effects,
and seamless multi-language market analysis.

Usage:
    streamlit run src/ui/app.py
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import streamlit as st

# =============================================================================
# PATH SETUP
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
CSS_PATH = Path(__file__).parent / "styles" / "dashboard.css"


# =============================================================================
# PAGE CONFIG — MUST BE FIRST STREAMLIT COMMAND
# =============================================================================

st.set_page_config(
    page_title="Market Intelligence Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# USER CONTEXT
# =============================================================================

from src.agents.user_context import setup_user_context

setup_user_context(
    name="Usuario",
    occupation="Data Science student",
    location="Medellín, Colombia",
    technical_level="intermediate",
    language="es",
    learning_goals="Aprender a analizar mercados financieros usando datos y machine learning",
)


# =============================================================================
# CSS
# =============================================================================


def _load_css() -> str:
    if "css_cached" not in st.session_state:
        try:
            st.session_state.css_cached = CSS_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            st.session_state.css_cached = ""
    return st.session_state.css_cached


st.markdown(f"<style>{_load_css()}</style>", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE
# =============================================================================


def _init() -> None:
    if "conversations" not in st.session_state:
        st.session_state.conversations = {}
    if "current_cid" not in st.session_state:
        st.session_state.current_cid = None
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = None


def _cid() -> str:
    return str(uuid.uuid4())[:8]


def _ensure_conversation() -> None:
    if not st.session_state.conversations:
        cid = _cid()
        st.session_state.conversations[cid] = {
            "id": cid, "title": "Nueva conversación", "messages": [],
        }
        st.session_state.current_cid = cid


def _conv() -> dict | None:
    cid = st.session_state.current_cid
    return st.session_state.conversations.get(cid) if cid else None


def _add_message(role: str, content: str) -> None:
    conv = _conv()
    if conv is None:
        cid = _cid()
        st.session_state.conversations[cid] = {
            "id": cid, "title": "Chat", "messages": [],
        }
        st.session_state.current_cid = cid
        conv = st.session_state.conversations[cid]
    conv["messages"].append({"role": role, "content": content})
    if role == "user" and conv["title"] in ("Nueva conversación", "Chat"):
        conv["title"] = (content[:42] + "…") if len(content) > 42 else content


# =============================================================================
# ORCHESTRATOR — Lazy init
# =============================================================================


def _get_orchestrator() -> Any:
    if st.session_state.orchestrator is None:
        try:
            from src.agents.orchestrator import MarketOrchestrator
            o = MarketOrchestrator()
            o.setup()
            st.session_state.orchestrator = o
        except Exception as e:
            st.error(f"System init failed: {e}")
            return None
    return st.session_state.orchestrator


# =============================================================================
# SIDEBAR — Conversation History
# =============================================================================


def _render_sidebar() -> None:
    with st.sidebar:
        if st.button("✨ New Chat", use_container_width=True, type="primary"):
            cid = _cid()
            st.session_state.conversations[cid] = {"id": cid, "title": "Nueva conversación", "messages": []}
            st.session_state.current_cid = cid
            st.rerun()

        convs = st.session_state.conversations
        if convs:
            for cid in list(convs.keys()):
                conv = convs[cid]
                active = cid == st.session_state.current_cid
                label = conv.get("title", "Untitled")

                # Active chat gets a prefix marker for CSS highlighting
                display_label = ("▸ " if active else "  ") + label
                cols = st.columns([5, 1])
                with cols[0]:
                    if st.button(display_label, key=f"c_{cid}", use_container_width=True, type="secondary"):
                        st.session_state.current_cid = cid
                        st.rerun()
                with cols[1]:
                    if st.button("✕", key=f"d_{cid}"):
                        del st.session_state.conversations[cid]
                        if st.session_state.conversations:
                            st.session_state.current_cid = list(st.session_state.conversations.keys())[0]
                        else:
                            _ensure_conversation()
                        st.rerun()

        st.markdown("---")
        st.caption("Market Intelligence Agent")
        st.caption("Multi-language · Equity Analysis · Real-time")


# =============================================================================
# WELCOME SCREEN
# =============================================================================

def _render_welcome() -> None:
    """Render welcome screen — clean, minimal, no suggestions."""
    st.markdown("""
    <div class="welcome">
        <span class="welcome-icon">✦</span>
        <span class="welcome-badge">AI-Powered · Multi-Language</span>
        <h1 class="welcome-title">Market Intelligence Agent</h1>
        <p class="welcome-subtitle">
            Pregunta sobre acciones, noticias financieras o sentimiento del mercado.<br>
            Te respondo en tu idioma — español, English, Français, Deutsch, and more.
        </p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# MAIN
# =============================================================================

_AVATARS = {
    "user": "◈",
    "assistant": "✦",
}


def main() -> None:
    _init()
    _ensure_conversation()
    _render_sidebar()

    conv = _conv()
    msgs = conv["messages"] if conv else []

    # --- Welcome screen (first visit, no messages) ---
    if not msgs:
        _render_welcome()

    # --- Chat messages ---
    for msg in msgs:
        with st.chat_message(msg["role"], avatar=_AVATARS.get(msg["role"], "🤖")):
            st.markdown(msg["content"])

    # --- Chat input ---
    prompt = st.chat_input("Pregunta sobre acciones, noticias o análisis de mercado...")
    if not prompt:
        return

    # User message
    _add_message("user", prompt)

    # Show it immediately
    with st.chat_message("user", avatar=_AVATARS["user"]):
        st.markdown(prompt)

    # Assistant response
    with st.chat_message("assistant", avatar=_AVATARS["assistant"]):
        with st.spinner(""):
            orch = _get_orchestrator()
            if orch:
                response = orch.ask(prompt)
            else:
                response = "⚠️ System unavailable. Check configuration."
        st.markdown(response)

    _add_message("assistant", response)
    st.rerun()


if __name__ == "__main__":
    main()
