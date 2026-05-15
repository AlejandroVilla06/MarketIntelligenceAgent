"""
Market Intelligence Agent - Agents Module

This module re-exports agent classes. Heavy dependencies are loaded lazily
to avoid import-time penalties (chromadb, sentence_transformers).
"""
from __future__ import annotations

# =============================================================================
# Legacy re-exports — point to market_orchestrator for hierarchical system
# =============================================================================
def __getattr__(name):
    if name == "MarketOrchestrator":
        from src.market_orchestrator.orchestrator import MarketOrchestrator as _o
        return _o

    # Existing agents (not duplicated)
    if name == "MarketRAGRetriever":
        from src.agents.retriever import MarketRAGRetriever
        return MarketRAGRetriever
    if name == "MarketQueryAgent":
        from src.agents.query_agent import MarketQueryAgent
        return MarketQueryAgent

    # Cache
    if name in ("get_cache_instance", "get_latency_tracker", "reset_cache", "SemanticCache", "CacheEntry", "LatencyMetrics"):
        from src.agents.cache import (
            get_cache_instance, get_latency_tracker, reset_cache,
            SemanticCache, CacheEntry, LatencyMetrics,
        )
        return locals()[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "MarketRAGRetriever",
    "MarketQueryAgent",
    "MarketOrchestrator",
    "get_cache_instance",
    "get_latency_tracker",
    "reset_cache",
    "SemanticCache",
    "CacheEntry",
    "LatencyMetrics",
]