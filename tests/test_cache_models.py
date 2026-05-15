"""
Tests for Cache Models - CacheEntry, LatencyMetrics
====================================================

Unit tests for cache data classes.

Run: python -m pytest tests/test_cache_models.py -v
"""

import time
import pytest
import sys
from pathlib import Path

# Direct import from models file - bypass agent imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import directly to avoid agent imports
import importlib.util
spec = importlib.util.spec_from_file_location(
    "cache_models",
    project_root / "src" / "agents" / "cache" / "models.py"
)
cache_models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cache_models)

CacheEntry = cache_models.CacheEntry
LatencyMetrics = cache_models.LatencyMetrics
AggregatedLatencyMetrics = cache_models.AggregatedLatencyMetrics


class TestCacheEntry:
    """Test CacheEntry serialization and TTL logic."""

    def test_cache_entry_creation(self):
        """Test creating a CacheEntry with all fields."""
        entry = CacheEntry(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
            response="test response",
            model_id="gpt-3.5-turbo",
            model_params={"temperature": 0.0},
            ttl_seconds=3600,
        )

        assert entry.query == "test query"
        assert entry.response == "test response"
        assert entry.model_id == "gpt-3.5-turbo"
        assert entry.model_params == {"temperature": 0.0}
        assert entry.ttl_seconds == 3600

    def test_cache_entry_defaults(self):
        """Test default values for CacheEntry."""
        entry = CacheEntry(
            query="test",
            query_embedding=[0.1],
            response="result",
            model_id="test-model",
        )

        assert entry.ttl_seconds == 86400  # 24 hours default
        assert entry.model_params == {}
        assert entry.metadata == {}

    def test_is_expired_false_when_no_ttl(self):
        """Test that entry with TTL=0 never expires."""
        entry = CacheEntry(
            query="test",
            query_embedding=[0.1],
            response="result",
            model_id="test",
            ttl_seconds=0,
        )

        assert entry.is_expired() is False

    def test_is_expired_false_when_fresh(self):
        """Test that recent entry is not expired."""
        entry = CacheEntry(
            query="test",
            query_embedding=[0.1],
            response="result",
            model_id="test",
            ttl_seconds=3600,  # 1 hour
            created_at=time.time(),
        )

        assert entry.is_expired() is False

    def test_is_expired_true_when_old(self):
        """Test that old entry is expired."""
        old_time = time.time() - 7200  # 2 hours ago
        entry = CacheEntry(
            query="test",
            query_embedding=[0.1],
            response="result",
            model_id="test",
            ttl_seconds=3600,  # 1 hour
            created_at=old_time,
        )

        assert entry.is_expired() is True

    def test_to_dict_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original = CacheEntry(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
            response={"key": "value"},
            model_id="gpt-4",
            model_params={"temperature": 0.7, "top_p": 0.9},
            ttl_seconds=7200,
        )

        data = original.to_dict()
        restored = CacheEntry.from_dict(data)

        assert restored.query == original.query
        assert restored.query_embedding == original.query_embedding
        assert restored.response == original.response
        assert restored.model_id == original.model_id
        assert restored.model_params == original.model_params
        assert restored.ttl_seconds == original.ttl_seconds


class TestLatencyMetrics:
    """Test LatencyMetrics timing and aggregation."""

    def test_latency_metrics_start(self):
        """Test starting a latency metrics."""
        metrics = LatencyMetrics.start("retrieval", {"query": "test"})

        assert metrics.operation == "retrieval"
        assert metrics.success is True
        assert metrics.end_time == 0.0
        assert metrics.duration_ms == 0.0

    def test_latency_metrics_finish(self):
        """Test finishing latency metrics calculates duration."""
        metrics = LatencyMetrics.start("test")
        time.sleep(0.01)  # 10ms
        metrics.finish(success=True)

        assert metrics.end_time > metrics.start_time
        assert metrics.duration_ms > 0
        assert metrics.success is True
        assert metrics.error_message is None

    def test_latency_metrics_finish_with_error(self):
        """Test finishing with error marks failure."""
        metrics = LatencyMetrics.start("test")
        metrics.finish(success=False, error="Something went wrong")

        assert metrics.success is False
        assert metrics.error_message == "Something went wrong"

    def test_latency_metrics_to_dict(self):
        """Test LatencyMetrics serialization."""
        metrics = LatencyMetrics.start("retrieval")
        metrics.finish(success=True)

        data = metrics.to_dict()

        assert data["operation"] == "retrieval"
        assert data["success"] is True
        assert "duration_ms" in data
        assert "start_time" in data
        assert "end_time" in data


class TestAggregatedLatencyMetrics:
    """Test AggregatedLatencyMetrics for percentiles."""

    def test_aggregated_add_samples(self):
        """Test adding samples to aggregated metrics."""
        agg = AggregatedLatencyMetrics(operation="test")

        for i in range(10):
            m = LatencyMetrics.start("test")
            m.finish(success=True)
            m.duration_ms = (i + 1) * 10  # 10, 20, ..., 100
            agg.add(m)

        assert agg.total_requests == 10
        assert agg.successful_requests == 10
        assert agg.failed_requests == 0

    def test_aggregated_percentiles(self):
        """Test percentile calculations."""
        agg = AggregatedLatencyMetrics(operation="test")

        # Add 100 samples from 1 to 100 ms
        for i in range(100):
            m = LatencyMetrics.start("test")
            m.finish(success=True)
            m.duration_ms = float(i + 1)
            agg.add(m)

        # p50 should be ~50ms, p90 should be ~90ms, p99 should be ~99ms
        assert 45 <= agg.get_percentile(50) <= 55
        assert 85 <= agg.get_percentile(90) <= 95
        assert 95 <= agg.get_percentile(99) <= 100

    def test_aggregated_to_dict(self):
        """Test aggregated metrics to dict with all stats."""
        agg = AggregatedLatencyMetrics(operation="retrieval")

        # Add some samples
        for i in range(5):
            m = LatencyMetrics.start("retrieval")
            m.finish(success=True)
            m.duration_ms = 50.0
            agg.add(m)

        data = agg.to_dict()

        assert data["operation"] == "retrieval"
        assert data["total_requests"] == 5
        assert data["successful_requests"] == 5
        assert "p50_ms" in data
        assert "p90_ms" in data
        assert "p99_ms" in data
        assert "mean_ms" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])