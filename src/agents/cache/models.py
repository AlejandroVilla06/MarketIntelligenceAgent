"""
Cache Models - Data Classes for RAG Semantic Cache
===========================================

Data classes for cache entries and latency metrics.

Usage:
    from src.agents.cache.models import CacheEntry, LatencyMetrics
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CacheEntry:
    """
    A single cache entry storing query, response, and metadata.

    Attributes:
        query: Original query text.
        query_embedding: Embedding vector for similarity comparison.
        response: Cached response (any serializable type).
        model_id: Model identifier used (e.g., "gpt-3.5-turbo").
        model_params: Model parameters (e.g., {"temperature": 0.0}).
        created_at: Unix timestamp when entry was created.
        ttl_seconds: Time-to-live in seconds (0 = never expires).
        metadata: Additional metadata dict.
    """
    query: str
    query_embedding: list[float]
    response: Any
    model_id: str
    model_params: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    ttl_seconds: int = 86400  # 24 hours default
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """
        Check if this entry has expired based on TTL.

        Returns:
            True if TTL > 0 and entry is older than ttl_seconds.
        """
        if self.ttl_seconds <= 0:
            return False
        age = time.time() - self.created_at
        return age > self.ttl_seconds

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for storage.

        Returns:
            Dictionary representation.
        """
        return {
            "query": self.query,
            "query_embedding": self.query_embedding,
            "response": self.response,
            "model_id": self.model_id,
            "model_params": self.model_params,
            "created_at": self.created_at,
            "ttl_seconds": self.ttl_seconds,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CacheEntry:
        """
        Create from dictionary.

        Args:
            data: Dictionary with cache entry fields.

        Returns:
            CacheEntry instance.
        """
        return cls(
            query=data["query"],
            query_embedding=data["query_embedding"],
            response=data["response"],
            model_id=data["model_id"],
            model_params=data.get("model_params", {}),
            created_at=data.get("created_at", time.time()),
            ttl_seconds=data.get("ttl_seconds", 86400),
            metadata=data.get("metadata", {}),
        )


@dataclass
class LatencyMetrics:
    """
    Latency metrics for a single operation or aggregated.

    Attributes:
        operation: Operation name (e.g., "retrieval", "generation").
        start_time: Unix timestamp when operation started.
        end_time: Unix timestamp when operation ended (0 if not finished).
        duration_ms: Duration in milliseconds.
        success: Whether operation succeeded.
        error_message: Error message if failed.
        metadata: Additional metadata dict.
    """
    operation: str
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    duration_ms: float = 0.0
    success: bool = True
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def finish(self, success: bool = True, error: str | None = None) -> None:
        """
        Mark the operation as finished and calculate duration.

        Args:
            success: Whether operation succeeded.
            error: Error message if failed.
        """
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.success = success
        self.error_message = error

    @classmethod
    def start(cls, operation: str, metadata: dict[str, Any] | None = None) -> LatencyMetrics:
        """
        Start a new latency tracking session.

        Args:
            operation: Operation name.
            metadata: Additional metadata.

        Returns:
            LatencyMetrics instance (not yet finished).
        """
        return cls(
            operation=operation,
            start_time=time.time(),
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "operation": self.operation,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


# =============================================================================
# AGGREGATED METRICS
# =============================================================================

@dataclass
class AggregatedLatencyMetrics:
    """
    Aggregated latency metrics for percentiles and summary.

    Attributes:
        operation: Operation name.
        durations_ms: List of individual durations.
        total_requests: Total number of requests.
        successful_requests: Number of successful requests.
        failed_requests: Number of failed requests.
    """
    operation: str
    durations_ms: list[float] = field(default_factory=list)
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    def add(self, metrics: LatencyMetrics) -> None:
        """
        Add a metrics sample.

        Args:
            metrics: LatencyMetrics to add.
        """
        if metrics.duration_ms > 0:
            self.durations_ms.append(metrics.duration_ms)
        self.total_requests += 1
        if metrics.success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

    def get_percentile(self, p: float) -> float:
        """
        Calculate percentile of durations.

        Args:
            p: Percentile (0-100), e.g., 50 for p50.

        Returns:
            Percentile value in ms, or 0.0 if no data.
        """
        if not self.durations_ms:
            return 0.0
        sorted_durations = sorted(self.durations_ms)
        idx = int(len(sorted_durations) * p / 100)
        idx = min(idx, len(sorted_durations) - 1)
        return sorted_durations[idx]

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary summary.

        Returns:
            Dictionary with p50, p90, p99, mean, min, max.
        """
        if not self.durations_ms:
            return {
                "operation": self.operation,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "p50_ms": 0.0,
                "p90_ms": 0.0,
                "p99_ms": 0.0,
                "mean_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
            }

        return {
            "operation": self.operation,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "p50_ms": round(self.get_percentile(50), 2),
            "p90_ms": round(self.get_percentile(90), 2),
            "p99_ms": round(self.get_percentile(99), 2),
            "mean_ms": round(sum(self.durations_ms) / len(self.durations_ms), 2),
            "min_ms": round(min(self.durations_ms), 2),
            "max_ms": round(max(self.durations_ms), 2),
        }


__all__ = [
    "CacheEntry",
    "LatencyMetrics",
    "AggregatedLatencyMetrics",
]