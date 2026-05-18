"""
Cache Module - RAG Latency Optimization
============================

Contains:
- models: CacheEntry, LatencyMetrics
- latency_tracker: Latency tracking decorators
- semantic_cache: Semantic cache with similarity lookup

Usage:
    from src.agents.cache import get_cache_instance, SemanticCache
    cache = get_cache_instance()
    cached = cache.get(query, model_id)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.agents.cache.models import CacheEntry, LatencyMetrics, AggregatedLatencyMetrics

if TYPE_CHECKING:
    from src.agents.cache.latency_tracker import LatencyTracker
    from src.agents.cache.semantic_cache import SemanticCache

# Lazy imports to avoid circular dependencies
_latency_tracker: LatencyTracker | None = None
_semantic_cache: SemanticCache | None = None


def get_latency_tracker() -> "LatencyTracker":
    """Get or create the LatencyTracker singleton."""
    global _latency_tracker
    if _latency_tracker is None:
        from src.agents.cache.latency_tracker import LatencyTracker
        _latency_tracker = LatencyTracker()
    return _latency_tracker


def get_cache_instance(
    similarity_threshold: float | None = None,
    ttl_seconds: int | None = None,
) -> SemanticCache:
    """Get or create the SemanticCache singleton.
    
    Args:
        similarity_threshold: Minimum similarity for cache hit (default: 0.85)
        ttl_seconds: Time-to-live in seconds (default: 86400 = 24h)
        
    Returns:
        SemanticCache singleton instance.
    """
    global _semantic_cache
    if _semantic_cache is None:
        from src.agents.cache.semantic_cache import SemanticCache
        from src.config import settings
        
        threshold = similarity_threshold or settings.cache_similarity_threshold
        ttl = ttl_seconds or settings.cache_ttl_seconds
        _semantic_cache = SemanticCache(
            similarity_threshold=threshold,
            ttl_seconds=ttl,
        )
    return _semantic_cache


def reset_cache() -> None:
    """Reset cache singletons (for testing)."""
    global _semantic_cache, _latency_tracker
    _semantic_cache = None
    _latency_tracker = None


__all__ = [
    "CacheEntry",
    "LatencyMetrics", 
    "AggregatedLatencyMetrics",
    "get_latency_tracker",
    "get_cache_instance",
    "reset_cache",
    "LatencyTracker",  # Re-export for type hints
    "SemanticCache",  # Re-export for type hints
]