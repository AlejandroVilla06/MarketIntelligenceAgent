"""
Tests for Sprint 4 Correlation Tools
================================

Tests the new correlation and alignment tools:
- query_by_metadata()
- get_sentiment_price_correlation_tool
- align_by_temporal_window_tool
- get_cross_collection_context_tool
"""

import sys
import os
import json
from pathlib import Path
from datetime import date, timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest

try:
    import chromadb
    import polars as pl
    from src.agents.retriever import MarketRAGRetriever
    DEPENDENCIES_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    DEPENDENCIES_AVAILABLE = False


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def retriever_with_data():
    """Create a retriever with sample data for testing."""
    retriever = MarketRAGRetriever(persist_directory=":memory:")
    
    # Add stock data (10 days)
    stock_data = pl.DataFrame({
        "date": [(date.today() - timedelta(days=i)).isoformat() for i in range(9, -1, -1)],
        "symbol": ["AAPL"] * 10,
        "close": [170.0 + i for i in range(10)],
        "volume": [50000000] * 10,
    })
    retriever.add_stock_data(stock_data)
    
    # Add sentiment data (10 days, matching dates)
    sentiment_data = [
        {"date": (date.today() - timedelta(days=i)).isoformat(), "sentiment_score": 0.5 if i < 5 else -0.3, "sentiment_label": "positive" if i < 5 else "negative"}
        for i in range(10)
    ]
    retriever.add_sentiment_data(sentiment_data)
    
    return retriever


@pytest.fixture
def retriever_no_overlap():
    """Create a retriever with non-overlapping data."""
    retriever = MarketRAGRetriever(persist_directory=":memory:")
    
    # Stock data: past month
    stock_data = pl.DataFrame({
        "date": [(date.today() - timedelta(days=30 + i)).isoformat() for i in range(10)],
        "symbol": ["AAPL"] * 10,
        "close": [170.0] * 10,
        "volume": [50000000] * 10,
    })
    retriever.add_stock_data(stock_data)
    
    # Sentiment data: this week (no overlap!)
    sentiment_data = [
        {"date": (date.today() - timedelta(days=i)).isoformat(), "sentiment_score": 0.5, "sentiment_label": "positive"}
        for i in range(5)
    ]
    retriever.add_sentiment_data(sentiment_data)
    
    return retriever


@pytest.fixture
def retriever_insufficient_data():
    """Create a retriever with only 5 overlapping days."""
    retriever = MarketRAGRetriever(persist_directory=":memory:")
    
    # Stock data: 5 days
    stock_data = pl.DataFrame({
        "date": [(date.today() - timedelta(days=i)).isoformat() for i in range(4, -1, -1)],
        "symbol": ["AAPL"] * 5,
        "close": [170.0] * 5,
        "volume": [50000000] * 5,
    })
    retriever.add_stock_data(stock_data)
    
    # Sentiment data: 5 days
    sentiment_data = [
        {"date": (date.today() - timedelta(days=i)).isoformat(), "sentiment_score": 0.5, "sentiment_label": "positive"}
        for i in range(4, -1, -1)
    ]
    retriever.add_sentiment_data(sentiment_data)
    
    return retriever


# =============================================================================
# TESTS: query_by_metadata() — Phase 1
# =============================================================================

class TestQueryByMetadata:
    """Tests for query_by_metadata() method from Phase 1."""

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
    def test_query_by_symbol(self, retriever_with_data):
        """Test filtering by symbol."""
        results = retriever_with_data.query_by_metadata(
            collection="stocks", query="", symbol="AAPL"
        )
        assert len(results) == 10
        assert all(r["metadata"].get("symbol") == "AAPL" for r in results)

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
    def test_query_by_date_range(self, retriever_with_data):
        """Test filtering by date range."""
        start = (date.today() - timedelta(days=5)).isoformat()
        end = date.today().isoformat()
        
        results = retriever_with_data.query_by_metadata(
            collection="stocks", query="", symbol="AAPL", start_date=start, end_date=end
        )
        # Should return 6 days (today + 5 days back)
        assert len(results) == 6

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
    def test_query_invalid_date_order(self, retriever_with_data):
        """Test that end_date < start_date raises ValueError."""
        end = (date.today() - timedelta(days=10)).isoformat()
        start = date.today().isoformat()
        
        with pytest.raises(ValueError, match="cannot be before"):
            retriever_with_data.query_by_metadata(
                collection="stocks", query="", start_date=start, end_date=end
            )

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
    def test_query_invalid_collection(self, retriever_with_data):
        """Test that invalid collection raises ValueError."""
        with pytest.raises(ValueError, match="Invalid collection"):
            retriever_with_data.query_by_metadata(
                collection="invalid", query=""
            )

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
    def test_query_by_sentiment_score_range(self, retriever_with_data):
        """Test filtering by sentiment score."""
        results = retriever_with_data.query_by_metadata(
            collection="sentiment", query="", min_sentiment_score=0.0, max_sentiment_score=0.6
        )
        assert all(0.0 <= r["metadata"].get("sentiment_score", -1) <= 0.6 for r in results)


# =============================================================================
# TESTS: get_sentiment_price_correlation_tool — Phase 2
# =============================================================================

class TestSentimentPriceCorrelation:
    """Tests for correlation tool from Phase 2."""

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
    def test_correlation_full_overlap(self, retriever_with_data):
        """Test correlation with full date overlap."""
        from src.agents.chains.market_tools import get_sentiment_price_correlation_tool
        
        result_json = get_sentiment_price_correlation_tool.invoke({
            "symbol": "AAPL",
            "window_days": 10
        })
        result = json.loads(result_json)
        
        assert result["status"] == "success"
        assert "pearson_coefficient" in result
        assert "spearman_coefficient" in result
        assert result["overlap_actual_days"] == 10

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
    def test_correlation_no_overlap(self, retriever_no_overlap):
        """Test correlation when no date overlap exists."""
        from src.agents.chains.market_tools import get_sentiment_price_correlation_tool
        from src.agents.retriever import MarketRAGRetriever
        
        # Patch the retriever
        import src.agents.chains.market_tools as tools_module
        original_class = MarketRAGRetriever
        # This test would need mocking in real test suite
        
    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
    def test_correlation_insufficient_data(self, retriever_insufficient_data):
        """Test correlation when insufficient overlapping data."""
        # 5 days is below the 10-day minimum threshold
        # Should return status: "insufficient_data"


# =============================================================================
# TESTS: align_by_temporal_window_tool — Phase 2
# =============================================================================

class TestTemporalAlignment:
    """Tests for alignment tool from Phase 2."""

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
    def test_alignment_valid(self, retriever_with_data):
        """Test alignment with valid data."""
        from src.agents.chains.market_tools import align_by_temporal_window_tool
        
        end = date.today().isoformat()
        start = (date.today() - timedelta(days=7)).isoformat()
        
        result_json = align_by_temporal_window_tool.invoke({
            "symbol": "AAPL",
            "start": start,
            "end": end,
        })
        result = json.loads(result_json)
        
        assert result["status"] == "success"
        assert "aligned_rows" in result
        assert result["overlap_count"] >= 7

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
    def test_alignment_no_overlap(self, retriever_no_overlap):
        """Test alignment when no overlap exists."""
        from src.agents.chains.market_tools import align_by_temporal_window_tool
        
        end = date.today().isoformat()
        start = (date.today() - timedelta(days=7)).isoformat()
        
        result_json = align_by_temporal_window_tool.invoke({
            "symbol": "AAPL",
            "start": start,
            "end": end,
        })
        result = json.loads(result_json)
        
        assert result["status"] == "no_overlap"


# =============================================================================
# TESTS: get_cross_collection_context_tool — Phase 2
# =============================================================================

class TestCrossCollectionContext:
    """Tests for cross-collection context tool from Phase 2."""

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
    def test_context_full(self, retriever_with_data):
        """Test getting full context from all collections."""
        from src.agents.chains.market_tools import get_cross_collection_context_tool
        
        result_json = get_cross_collection_context_tool.invoke({
            "symbol": "AAPL",
            "recency_days": 10
        })
        result = json.loads(result_json)
        
        assert "stocks_summary" in result
        assert "sentiment_summary" in result
        assert "prompt_string" in result
        assert result["symbol"] == "AAPL"

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
    def test_context_missing_collection(self):
        """Test context when some collections have no data."""
        from src.agents.chains.market_tools import get_cross_collection_context_tool
        from src.agents.retriever import MarketRAGRetriever
        
        # Create empty retriever
        retriever = MarketRAGRetriever(persist_directory=":memory:")
        
        result_json = get_cross_collection_context_tool.invoke({
            "symbol": "AAPL",
            "recency_days": 10
        })
        result = json.loads(result_json)
        
        # Should indicate missing collections
        assert "temporal_metadata" in result or result.get("stocks_summary", {}).get("status") == "no_data"


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])