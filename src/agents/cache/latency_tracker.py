"""
Latency Tracker - RAG Latency Benchmarking
=======================================

Decorators and classes for tracking operation latencies.

Usage:
    from src.agents.cache.latency_tracker import LatencyTracker, track_latency
    
    tracker = LatencyTracker()
    
    @track_latency("retrieval")
    def my_function():
        # ... do work ...
        pass
"""

from __future__ import annotations

import functools
import time
from collections import defaultdict
from typing import Any, Callable, TypeVar

from src.agents.cache.models import AggregatedLatencyMetrics, LatencyMetrics

# Type variable for decorator
F = TypeVar("F", bound=Callable[..., Any])


class LatencyTracker:
    """
    Centralized latency tracking for RAG operations.
    
    Tracks individual operations and aggregates metrics for percentiles.
    Thread-safe for concurrent access.
    
    Usage:
        tracker = LatencyTracker()
        tracker.start("retrieval")
        # ... do work ...
        tracker.finish("retrieval", success=True)
        
        summary = tracker.get_metrics_summary()
    """
    
    def __init__(self) -> None:
        """Initialize latency tracker."""
        self._metrics: dict[str, AggregatedLatencyMetrics] = defaultdict(
            lambda: AggregatedLatencyMetrics(operation="")
        )
        self._current: dict[str, LatencyMetrics] = {}
    
    def start(self, operation: str, metadata: dict[str, Any] | None = None) -> LatencyMetrics:
        """
        Start tracking an operation.
        
        Args:
            operation: Operation name (e.g., "retrieval", "generation").
            metadata: Optional metadata dict.
            
        Returns:
            LatencyMetrics instance.
        """
        metrics = LatencyMetrics.start(operation, metadata)
        self._current[operation] = metrics
        return metrics
    
    def finish(
        self,
        operation: str,
        success: bool = True,
        error: str | None = None,
    ) -> LatencyMetrics | None:
        """
        Finish tracking an operation.
        
        Args:
            operation: Operation name.
            success: Whether operation succeeded.
            error: Error message if failed.
            
        Returns:
            LatencyMetrics instance, or None if not started.
        """
        metrics = self._current.pop(operation, None)
        if metrics is None:
            return None
        
        metrics.finish(success=success, error=error)
        self._metrics[operation].add(metrics)
        return metrics
    
    def get_metrics_summary(self, operation: str | None = None) -> dict[str, Any]:
        """
        Get metrics summary for one or all operations.
        
        Args:
            operation: Specific operation, or None for all.
            
        Returns:
            Dict with metrics summaries.
        """
        if operation:
            agg = self._metrics.get(operation)
            if agg:
                return agg.to_dict()
            return {}
        
        return {
            op: agg.to_dict()
            for op, agg in self._metrics.items()
        }
    
    def reset(self, operation: str | None = None) -> None:
        """
        Reset metrics for one or all operations.
        
        Args:
            operation: Specific operation, or None for all.
        """
        if operation:
            self._metrics.pop(operation, None)
            self._current.pop(operation, None)
        else:
            self._metrics.clear()
            self._current.clear()
    
    def __repr__(self) -> str:
        ops = list(self._metrics.keys())
        return f"LatencyTracker(operations={ops})"


# =============================================================================
# DECORATOR
# =============================================================================

def track_latency(operation: str) -> Callable[[F], F]:
    """
    Decorator to track latency of a function.
    
    Usage:
        @track_latency("retrieval")
        def query_db(q):
            return db.query(q)
    
    Args:
        operation: Operation name for metrics.
        
    Returns:
        Decorated function.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracker = _get_global_tracker()
            metrics = tracker.start(operation)
            try:
                result = func(*args, **kwargs)
                tracker.finish(operation, success=True)
                return result
            except Exception as e:
                tracker.finish(operation, success=False, error=str(e))
                raise
        
        return wrapper  # type: ignore[return-value]
    return decorator


# =============================================================================
# GLOBAL TRACKER
# =============================================================================

_tracker: LatencyTracker | None = None


def _get_global_tracker() -> LatencyTracker:
    """Get or create the global LatencyTracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = LatencyTracker()
    return _tracker


def get_latency_tracker() -> LatencyTracker:
    """
    Get the global LatencyTracker instance.
    
    Returns:
        LatencyTracker singleton.
    """
    return _get_global_tracker()


__all__ = [
    "LatencyTracker",
    "track_latency",
    "get_latency_tracker",
    "LatencyMetrics",
    "AggregatedLatencyMetrics",
]