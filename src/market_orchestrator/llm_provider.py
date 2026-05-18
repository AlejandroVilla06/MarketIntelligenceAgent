"""
Shared LLM provider — singleton ChatOpenAI instance for all sub-orchestrators.

Prevents duplicate LLM initialization (~1.3s each) across Crypto, Macro,
Stocks, and Router agents. Also forces the heavy langchain_openai import
(~8s) at startup time instead of on the first user request.
"""
from __future__ import annotations

from langchain_openai import ChatOpenAI
from src.config import settings

_llm: ChatOpenAI | None = None


def get_llm() -> ChatOpenAI | None:
    """Get or create the shared LLM instance (lazy singleton).

    The first call triggers the heavy import of langchain_openai (~8s).
    Subsequent calls reuse the cached instance.

    Returns:
        ChatOpenAI instance configured from settings, or None if setup fails.
    """
    global _llm
    if _llm is None:
        try:
            _llm = ChatOpenAI(
                model=settings.rag_llm_model,
                temperature=0.3,
                api_key=settings.openai_api_key,
                base_url=settings.openai_api_base,
            )
        except Exception as e:
            import logging
            logging.getLogger("agents.llm_provider").warning(
                "Failed to initialize LLM: %s", e
            )
            _llm = False  # Sentinel
    return _llm if _llm is not False else None


def warmup_llm() -> None:
    """Force LLM initialization at startup (pre-calentamiento).

    Call this during MarketOrchestrator.setup() so the ~8s import
    happens at server start, NOT on the first user message.
    """
    get_llm()


__all__ = ["get_llm", "warmup_llm"]
