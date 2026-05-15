"""
Market Intelligence Agent - Agents Module
=========================================

Exports agent classes for market data retrieval and querying.

Usage:
    from src.agents import MarketRAGRetriever, MarketQueryAgent, MarketOrchestrator
    from src.agents import get_cache_instance, SemanticCache
"""

try:
    from src.agents.retriever import (
        EMBEDDING_MODEL,
        COLLECTION_STOCKS,
        COLLECTION_NEWS,
        COLLECTION_SENTIMENT,
        MarketRAGRetriever,
    )
except ImportError:
    # retriever has heavy deps (chromadb, sentence-transformers)
    MarketRAGRetriever = None
    EMBEDDING_MODEL = None
    COLLECTION_STOCKS = None
    COLLECTION_NEWS = None
    COLLECTION_SENTIMENT = None

try:
    from src.agents.query_agent import MarketQueryAgent
except ImportError:
    MarketQueryAgent = None

try:
    from src.agents.orchestrator import MarketOrchestrator
except ImportError:
    MarketOrchestrator = None

# Cache module exports (lazy imports to avoid langchain dependency issues)
try:
    from src.agents.cache import (
        get_cache_instance,
        get_latency_tracker,
        reset_cache,
        SemanticCache,
        CacheEntry,
        LatencyMetrics,
    )
    _CACHE_AVAILABLE = True
except ImportError:
    _CACHE_AVAILABLE = False
    get_cache_instance = None
    get_latency_tracker = None
    reset_cache = None
    SemanticCache = None
    CacheEntry = None
    LatencyMetrics = None

__all__ = [
    "MarketRAGRetriever",
    "MarketQueryAgent",
    "MarketOrchestrator",
    "EMBEDDING_MODEL",
    "COLLECTION_STOCKS",
    "COLLECTION_NEWS",
    "COLLECTION_SENTIMENT",
    # Cache exports
    "get_cache_instance",
    "get_latency_tracker",
    "reset_cache",
    "SemanticCache",
    "CacheEntry",
    "LatencyMetrics",
]