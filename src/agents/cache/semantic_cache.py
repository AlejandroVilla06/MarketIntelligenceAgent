"""
Semantic Cache - RAG Query Cache with Semantic Similarity
==================================================

High-level semantic cache with similarity lookup.

Usage:
    from src.agents.cache.semantic_cache import SemanticCache
    
    cache = SemanticCache(similarity_threshold=0.85, ttl_seconds=86400)
    
    # Get cached response
    cached = cache.get(query, model_id)
    if cached:
        return cached.response
    
    # Store new response
    cache.set(query, response, model_id)
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Any

from src.agents.cache.chroma_cache_store import ChromaCacheStore
from src.agents.cache.models import CacheEntry
from src.config import settings

logger = logging.getLogger(__name__)


class SemanticCache:
    """
    Semantic cache for RAG query responses.
    
    Caches query responses and retrieves them using semantic similarity.
    Uses ChromaDB for storage and cosine similarity for lookup.
    
    Usage:
        cache = SemanticCache()
        cached = cache.get("AAPL news", "gpt-3.5-turbo")
        if cached:
            print("Cache hit!", cached.response)
        else:
            response = llm.generate("AAPL news")
            cache.set("AAPL news", response, "gpt-3.5-turbo")
    """
    
    def __init__(
        self,
        similarity_threshold: float | None = None,
        ttl_seconds: int | None = None,
        persist_directory: str | None = None,
        hot_cache_size: int = 100,
    ) -> None:
        """
        Initialize semantic cache.
        
        Args:
            similarity_threshold: Minimum similarity for cache hit (0.0-1.0).
            ttl_seconds: Time-to-live in seconds (0 = never expires).
            persist_directory: ChromaDB persistence directory.
            hot_cache_size: Maximum entries in the in-memory LRU hot cache.
        """
        self.similarity_threshold = (
            similarity_threshold 
            or settings.cache_similarity_threshold
        )
        self.ttl_seconds = (
            ttl_seconds 
            or settings.cache_ttl_seconds
        )
        self._enabled = settings.cache_enabled
        
        # Initialize storage
        self._store = ChromaCacheStore(persist_directory)
        
        # Embedding function (shared singleton)
        self._embedding_function = None
        
        # In-memory LRU hot cache (fast layer before ChromaDB)
        self._hot_cache: OrderedDict = OrderedDict()
        self._hot_cache_max = hot_cache_size
    
    def _get_embedding_function(self):
        """Lazy load embedding function (shared singleton)."""
        if self._embedding_function is None:
            from src.agents.embedding import get_embedding_model
            self._embedding_function = get_embedding_model()
        return self._embedding_function
    
    def _embed(self, text: str) -> list[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed.
            
        Returns:
            Embedding vector.
        """
        model = self._get_embedding_function()
        return model.encode([text])[0].tolist()
    
    def get(
        self,
        query: str,
        model_id: str,
        model_params: dict[str, Any] | None = None,
    ) -> CacheEntry | None:
        """
        Get cached response for query.
        
        Args:
            query: Query text.
            model_id: Model identifier.
            model_params: Model parameters for cache key.
            
        Returns:
            CacheEntry if found and valid, None otherwise.
        """
        if not self._enabled:
            return None

        # 1. Check in-memory hot cache first (fastest — no embedding needed)
        hot_key = f"{query}:{model_id}"
        if hot_key in self._hot_cache:
            entry = self._hot_cache[hot_key]
            if not entry.is_expired():
                logger.info("Hot cache HIT: %s...", query[:50])
                # Promote to MRU (most recently used) position
                self._hot_cache.move_to_end(hot_key)
                return entry
            # Expired — remove from hot cache
            del self._hot_cache[hot_key]

        # 2. Check ChromaDB (slower — requires embedding)
        query_embedding = self._embed(query)
        cached = self._store.get_similar(
            query_embedding,
            threshold=self.similarity_threshold,
        )

        # Check model match (model_id AND model_params must match)
        if cached and cached.model_id == model_id:
            # Compare model params if provided
            if model_params:
                cached_params = cached.model_params or {}
                # If params don't match, don't return cached result
                if cached_params != model_params:
                    return None
            # Promote to hot cache for future fast lookups
            self._hot_cache[hot_key] = cached
            # Evict oldest if at capacity
            if len(self._hot_cache) > self._hot_cache_max:
                self._hot_cache.popitem(last=False)
            return cached

        return None
    
    def set(
        self,
        query: str,
        response: Any,
        model_id: str,
        model_params: dict[str, Any] | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        """
        Store query response in cache.
        
        Args:
            query: Query text.
            response: Response to cache (must be serializable).
            model_id: Model identifier.
            model_params: Model parameters.
            ttl_seconds: Override TTL (uses default if None).
        """
        if not self._enabled:
            return
        
        # Embed query
        query_embedding = self._embed(query)
        
        # Create entry
        entry = CacheEntry(
            query=query,
            query_embedding=query_embedding,
            response=response,
            model_id=model_id,
            model_params=model_params or {},
            ttl_seconds=ttl_seconds or self.ttl_seconds,
        )
        
        # Store in ChromaDB (persistent)
        self._store.put(entry)
        
        # Also store in hot cache (fast in-memory)
        hot_key = f"{query}:{model_id}"
        self._hot_cache[hot_key] = entry
        # Evict oldest if at capacity
        if len(self._hot_cache) > self._hot_cache_max:
            self._hot_cache.popitem(last=False)
    
    def invalidate(
        self,
        pattern: str | None = None,
        model_id: str | None = None,
    ) -> int:
        """
        Invalidate cache entries.
        
        Args:
            pattern: Query pattern to match (simple contains).
            model_id: Specific model to invalidate.
            
        Returns:
            Number of entries invalidated.
        """
        if not self._enabled:
            return 0
        
        # For now, simplified - clear all if pattern given
        if pattern or model_id:
            # This would require a full scan - skip for now
            return 0
        
        self._store.clear()
        return 1
    
    def clear(self) -> None:
        """Clear all cache entries (both hot cache and ChromaDB)."""
        if self._enabled:
            self._hot_cache.clear()
            self._store.clear()
    
    def clear_hot_cache(self) -> None:
        """Clear only the in-memory hot cache (ChromaDB is untouched)."""
        self._hot_cache.clear()
    
    @property
    def enabled(self) -> bool:
        """Check if cache is enabled."""
        return self._enabled
    
    def __repr__(self) -> str:
        return (
            f"SemanticCache("
            f"enabled={self._enabled}, "
            f"threshold={self.similarity_threshold}, "
            f"ttl={self.ttl_seconds})"
        )


# =============================================================================
# SINGLETON REGISTRY
# =============================================================================

_cache_instance: SemanticCache | None = None


def get_cache_instance(
    similarity_threshold: float | None = None,
    ttl_seconds: int | None = None,
) -> SemanticCache:
    """
    Get or create the SemanticCache singleton.
    
    Args:
        similarity_threshold: Minimum similarity for cache hit.
        ttl_seconds: Time-to-live in seconds.
        
    Returns:
        SemanticCache instance.
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SemanticCache(
            similarity_threshold= similarity_threshold,
            ttl_seconds=ttl_seconds,
        )
    return _cache_instance


def reset_cache() -> None:
    """Reset cache singleton (for testing)."""
    global _cache_instance
    if _cache_instance:
        _cache_instance.clear()
    _cache_instance = None


__all__ = [
    "SemanticCache",
    "get_cache_instance",
    "reset_cache",
]