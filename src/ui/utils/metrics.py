"""
UI Utilities - Metrics Retrieval Functions
============================================

Helper functions for retrieving system metrics to display in the UI.

Functions:
    get_ollama_status: Check Ollama connection status
    get_cache_stats: Get cache statistics
    get_document_counts: Get document counts from ChromaDB
    get_latency_metrics: Get latency benchmarks from tracker

Usage:
    from src.ui.utils.metrics import get_ollama_status, get_latency_metrics
    
    status = get_ollama_status()
    metrics = get_latency_metrics()
"""

from __future__ import annotations

from typing import Any

from src.config import settings


def get_ollama_status() -> dict[str, Any]:
    """
    Check Ollama connection status.
    
    Attempts to connect to the Ollama host and retrieve available models.
    
    Returns:
        dict with keys:
        - status: "connected" | "disconnected" | "unavailable"
        - models: list of available models (if connected)
        - model_count: number of models (if connected)
        - error: error message (if not connected)
    """
    try:
        import httpx
        response = httpx.get(
            f"{settings.ollama_host}/api/tags",
            timeout=3.0,
        )
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {
                "status": "connected",
                "models": models,
                "model_count": len(models),
            }
        return {
            "status": "disconnected",
            "error": f"Status: {response.status_code}",
        }
    except Exception as e:
        return {
            "status": "unavailable",
            "error": str(e),
        }


def get_cache_stats() -> dict[str, Any]:
    """
    Get cache statistics from the semantic cache.
    
    Returns:
        dict with keys:
        - enabled: bool
        - hits: int (if available)
        - misses: int (if available)
        - hit_rate: float (if available)
        - error: str (if failed)
    """
    if not settings.cache_enabled:
        return {"enabled": False}
    
    try:
        from src.agents.cache import get_cache_instance
        
        get_cache_instance()
        # Get stats from cache store if available
        # This is implementation-dependent
        
        return {
            "enabled": True,
            "ttl_seconds": settings.cache_ttl_seconds,
            "similarity_threshold": settings.cache_similarity_threshold,
        }
    except Exception as e:
        return {
            "enabled": True,
            "error": str(e),
        }


def get_document_counts(orchestrator: Any | None = None) -> dict[str, int]:
    """
    Get document counts from ChromaDB collections.
    
    Args:
        orchestrator: MarketOrchestrator instance (optional)
    
    Returns:
        dict with keys: stocks, news, sentiment
    """
    counts = {
        "stocks": 0,
        "news": 0,
        "sentiment": 0,
    }
    
    if orchestrator is None:
        return counts
    
    try:
        if orchestrator.retriever:
            status = orchestrator.get_status()
            counts = status.get("counts", counts)
    except Exception:
        pass
    
    return counts


def get_latency_metrics() -> dict[str, Any] | None:
    """
    Get latency metrics from the latency tracker.
    
    Returns:
        dict with keys: avg_ttft_ms, avg_total_ms, p50, p90, p99, sample_count
        or None if no metrics available
    """
    try:
        from src.agents.cache.latency_tracker import LatencyTracker
        
        tracker = LatencyTracker()
        summary = tracker.get_metrics_summary()
        
        if summary and summary.get("total_queries", 0) > 0:
            return {
                "avg_ttft_ms": round(summary.get("avg_ttft", 0), 2),
                "avg_total_ms": round(summary.get("avg_total", 0), 2),
                "p50": round(summary.get("p50", 0), 2),
                "p90": round(summary.get("p90", 0), 2),
                "p99": round(summary.get("p99", 0), 2),
                "sample_count": summary.get("total_queries", 0),
            }
        return None
    except Exception:
        return None


__all__ = [
    "get_ollama_status",
    "get_cache_stats",
    "get_document_counts",
    "get_latency_metrics",
]