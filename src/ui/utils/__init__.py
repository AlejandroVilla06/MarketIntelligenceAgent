"""
UI Utilities Module
==================

Utility functions for the Streamlit UI.
"""

from src.ui.utils.metrics import (
    get_ollama_status,
    get_cache_stats,
    get_document_counts,
    get_latency_metrics,
)

__all__ = [
    "get_ollama_status",
    "get_cache_stats",
    "get_document_counts",
    "get_latency_metrics",
]