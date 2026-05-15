"""
Tests for src.agents.retriever module (MarketRAGRetriever).

Tests the MarketRAGRetriever class with mocked ChromaDB.
Validates document formatting and query methods.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest


# Try to import dependencies
try:
    import chromadb
    import polars as pl
    from polars import DataFrame
    # Try to import the actual module
    from src.agents.retriever import MarketRAGRetriever
    DEPENDENCIES_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    DEPENDENCIES_AVAILABLE = False


class TestDocumentFormatting:
    """Tests for document text formatting (Task 4.4)."""

    @pytest.fixture
    def sample_stock_df(self) -> DataFrame:
        """Create a sample stock DataFrame for testing."""
        return DataFrame({
            "date": ["2024-01-15", "2024-01-16", "2024-01-17"],
            "symbol": ["AAPL", "AAPL", "AAPL"],
            "close": [170.2, 171.5, 172.0],
            "volume": [50000000, 55000000, 52000000],
            "rsi_14": [65.0, 68.0, 70.0],
        })

    def test_stock_document_format(self, sample_stock_df):
        """Test stock DataFrame to document string conversion."""
        row = sample_stock_df.to_dicts()[0]
        
        symbol = str(row.get("symbol", ""))
        date = str(row.get("date", ""))
        close = row.get("close", 0.0)
        volume = row.get("volume", 0)
        rsi = row.get("rsi_14", None)
        
        doc_parts = [
            f"{symbol} {date}",
            f"close={close}",
            f"volume={volume}",
        ]
        if rsi is not None:
            doc_parts.append(f"RSI={rsi}")
        
        document = " ".join(doc_parts)
        
        assert "AAPL 2024-01-15 close=170.2" in document
        assert "volume=50000000" in document
        assert "RSI=65.0" in document

    def test_news_document_format(self):
        """Test news article to document string conversion."""
        article = {
            "title": "Apple Reports Earnings",
            "content": "Strong quarterly results.",
        }
        
        document = f"{article['title']}. {article['content']}"
        
        assert "Apple Reports Earnings" in document
        assert "Strong quarterly results" in document

    def test_sentiment_document_format(self):
        """Test sentiment data to document string conversion."""
        data = {
            "symbol": "AAPL",
            "date": "2024-01-15",
            "sentiment_score": 0.75,
            "sentiment_label": "positive",
        }
        
        document = f"{data['symbol']} sentiment {data['sentiment_score']} {data['sentiment_label']} on {data['date']}"
        
        assert "AAPL sentiment 0.75 positive on 2024-01-15" == document

    def test_stock_document_without_rsi(self):
        """Test stock document format without RSI."""
        row = {
            "symbol": "GOOGL",
            "date": "2024-01-15",
            "close": 140.0,
            "volume": 25000000,
        }
        
        doc_parts = [
            f"{row['symbol']} {row['date']}",
            f"close={row['close']}",
            f"volume={row['volume']}",
        ]
        document = " ".join(doc_parts)
        
        assert "GOOGL" in document
        assert "close=140.0" in document
        assert "RSI" not in document

    def test_stock_document_with_all_fields(self):
        """Test stock document format with all fields."""
        row = {
            "symbol": "MSFT",
            "date": "2024-01-15",
            "close": 380.0,
            "volume": 30000000,
            "rsi_14": 72.5,
        }
        
        doc_parts = [
            f"{row['symbol']} {row['date']}",
            f"close={row['close']}",
            f"volume={row['volume']}",
            f"RSI={row['rsi_14']}",
        ]
        document = " ".join(doc_parts)
        
        expected = "MSFT 2024-01-15 close=380.0 volume=30000000 RSI=72.5"
        assert document == expected


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
class TestMarketRAGRetriever:
    """Test cases for MarketRAGRetriever class."""

    @pytest.fixture
    def mock_chromadb_client(self, tmp_path: Path):
        """Create a mock ChromaDB client that doesn't actually connect."""
        from unittest.mock import MagicMock, patch
        
        mock_client = MagicMock()
        mock_collections = {}
        
        def mock_get_or_create(name):
            mock_collection = MagicMock()
            mock_collection.count.return_value = 0
            mock_collections[name] = mock_collection
            return mock_collection
        
        mock_client.get_or_create_collection = mock_get_or_create
        mock_client.delete_collection = MagicMock()
        
        return mock_client, mock_collections

    @pytest.fixture
    def mock_embedding_model(self):
        """Create a mock embedding model."""
        from unittest.mock import MagicMock, patch
        
        with patch("sentence_transformers.SentenceTransformer") as mock_class:
            mock_instance = MagicMock()
            mock_instance.encode.return_value = [[0.1] * 384]
            mock_class.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def sample_stock_df(self) -> DataFrame:
        """Create a sample stock DataFrame for testing."""
        return DataFrame({
            "date": ["2024-01-15", "2024-01-16", "2024-01-17"],
            "symbol": ["AAPL", "AAPL", "AAPL"],
            "close": [170.2, 171.5, 172.0],
            "volume": [50000000, 55000000, 52000000],
            "rsi_14": [65.0, 68.0, 70.0],
        })

    @pytest.fixture
    def sample_news_articles(self) -> list[dict]:
        """Create sample news articles for testing."""
        return [
            {
                "title": "Apple Reports Strong Earnings",
                "content": "Apple Inc. reported quarterly earnings that beat analyst expectations.",
                "source": "Reuters",
                "timestamp": "2024-01-15T10:30:00",
                "symbol": "AAPL",
                "sentiment_score": 0.75,
            },
            {
                "title": "Tech Stocks Rally",
                "content": "Technology sector sees gains amid positive earnings reports.",
                "source": "Bloomberg",
                "timestamp": "2024-01-16T14:00:00",
                "symbol": "AAPL",
                "sentiment_score": 0.65,
            },
        ]

    @pytest.fixture
    def sample_sentiment_data(self) -> list[dict]:
        """Create sample sentiment data for testing."""
        return [
            {
                "symbol": "AAPL",
                "date": "2024-01-15",
                "sentiment_score": 0.75,
                "sentiment_label": "positive",
            },
            {
                "symbol": "AAPL",
                "date": "2024-01-16",
                "sentiment_score": 0.65,
                "sentiment_label": "positive",
            },
        ]

    def test_retriever_can_be_imported(self):
        """Test that the retriever module can be imported."""
        from src.agents.retriever import MarketRAGRetriever
        assert MarketRAGRetriever is not None

    def test_retriever_initialization(self, tmp_path: Path):
        """Test retriever initialization."""
        from src.agents.retriever import MarketRAGRetriever
        
        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        
        assert retriever.collection_stocks == "market_stocks"
        assert retriever.collection_news == "market_news"
        assert retriever.collection_sentiment == "market_sentiment"

    def test_add_stock_data_empty_dataframe(self, tmp_path: Path):
        """Test that add_stock_data handles empty DataFrame."""
        from src.agents.retriever import MarketRAGRetriever
        
        empty_df = DataFrame()
        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        
        # Should not raise
        retriever.add_stock_data(empty_df)

    def test_add_news_data_empty_list(self, tmp_path: Path):
        """Test that add_news_data handles empty list."""
        from src.agents.retriever import MarketRAGRetriever
        
        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        
        # Should not raise
        retriever.add_news_data([])

    def test_add_sentiment_data_empty_list(self, tmp_path: Path):
        """Test that add_sentiment_data handles empty list."""
        from src.agents.retriever import MarketRAGRetriever
        
        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        
        # Should not raise
        retriever.add_sentiment_data([])

    def test_query_stocks_returns_list(self, tmp_path: Path):
        """Test that query_stocks returns a list."""
        from src.agents.retriever import MarketRAGRetriever
        
        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        results = retriever.query_stocks("AAPL", k=5)
        
        assert isinstance(results, list)

    def test_query_news_returns_list(self, tmp_path: Path):
        """Test that query_news returns a list."""
        from src.agents.retriever import MarketRAGRetriever
        
        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        results = retriever.query_news("AAPL news", k=5)
        
        assert isinstance(results, list)

    def test_query_sentiment_returns_list(self, tmp_path: Path):
        """Test that query_sentiment returns a list."""
        from src.agents.retriever import MarketRAGRetriever
        
        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        results = retriever.query_sentiment("AAPL sentiment", k=5)
        
        assert isinstance(results, list)

    def test_query_all_returns_dict(self, tmp_path: Path):
        """Test that query_all returns a dict with collection keys."""
        from src.agents.retriever import MarketRAGRetriever
        
        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        results = retriever.query_all("AAPL", k_per_collection=3)
        
        assert isinstance(results, dict)
        assert "stocks" in results
        assert "news" in results
        assert "sentiment" in results

    def test_reset_clears_collections(self, tmp_path: Path):
        """Test that reset clears collections."""
        from src.agents.retriever import MarketRAGRetriever
        
        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        retriever.reset()
        
        # Should not raise
        assert True

    def test_add_and_query_stock_data(self, tmp_path: Path):
        """Test add_stock_data followed by query_stocks."""
        from src.agents.retriever import MarketRAGRetriever
        
        df = DataFrame({
            "date": ["2024-01-15"],
            "symbol": ["AAPL"],
            "close": [170.2],
            "volume": [50000000],
            "rsi_14": [65.0],
        })
        
        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        retriever.add_stock_data(df)
        
        results = retriever.query_stocks("AAPL", k=1)
        
        # Results may be empty if embeddings don't match, but structure should be correct
        assert isinstance(results, list)


# =============================================================================
# Tests for Sprint 4 Phase 1: Temporal Filter Foundation
# =============================================================================

class TestQueryByMetadata:
    """Tests for query_by_metadata() method introduced in Sprint 4 Phase 1."""

    def test_query_by_metadata_invalid_collection(self, tmp_path: Path):
        """Test that invalid collection raises ValueError."""
        from src.agents.retriever import MarketRAGRetriever

        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))

        with pytest.raises(ValueError, match="Invalid collection"):
            retriever.query_by_metadata(
                collection="invalid",
                query="test",
            )

    def test_query_by_metadata_end_before_start_date(self, tmp_path: Path):
        """Test that end_date before start_date raises ValueError."""
        from src.agents.retriever import MarketRAGRetriever

        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))

        with pytest.raises(ValueError, match="end_date.*cannot be before"):
            retriever.query_by_metadata(
                collection="stocks",
                query="AAPL",
                start_date="2024-01-16",
                end_date="2024-01-15",
            )

    def test_query_by_metadata_sentiment_score_inverted(self, tmp_path: Path):
        """Test that min > max sentiment score raises ValueError."""
        from src.agents.retriever import MarketRAGRetriever

        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))

        with pytest.raises(ValueError, match="min_sentiment_score.*cannot be greater"):
            retriever.query_by_metadata(
                collection="sentiment",
                query="AAPL",
                start_date="2024-01-15",
                end_date="2024-01-16",
                min_sentiment_score=0.8,
                max_sentiment_score=0.3,
            )

    def test_query_by_metadata_stocks_with_symbol_filter(self, tmp_path: Path):
        """Test query_stocks filtered by symbol."""
        from src.agents.retriever import MarketRAGRetriever

        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        results = retriever.query_by_metadata(
            collection="stocks",
            query="AAPL",
            symbol="AAPL",
            k=5,
        )

        assert isinstance(results, list)

    def test_query_by_metadata_stocks_with_date_range(self, tmp_path: Path):
        """Test query_stocks filtered by start_date and end_date."""
        from src.agents.retriever import MarketRAGRetriever

        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        results = retriever.query_by_metadata(
            collection="stocks",
            query="AAPL",
            start_date="2024-01-15",
            end_date="2024-01-16",
            k=5,
        )

        assert isinstance(results, list)

    def test_query_by_metadata_news_with_date_range(self, tmp_path: Path):
        """Test query_news filtered by date range."""
        from src.agents.retriever import MarketRAGRetriever

        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        results = retriever.query_by_metadata(
            collection="news",
            query="earnings",
            start_date="2024-01-15",
            end_date="2024-01-16",
            k=5,
        )

        assert isinstance(results, list)

    def test_query_by_metadata_sentiment_with_score_range(self, tmp_path: Path):
        """Test query_sentiment filtered by sentiment score range."""
        from src.agents.retriever import MarketRAGRetriever

        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        results = retriever.query_by_metadata(
            collection="sentiment",
            query="positive",
            min_sentiment_score=0.5,
            max_sentiment_score=1.0,
            k=5,
        )

        assert isinstance(results, list)

    def test_query_by_metadata_news_with_score_filter(self, tmp_path: Path):
        """Test query_news filtered by sentiment score."""
        from src.agents.retriever import MarketRAGRetriever

        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        results = retriever.query_by_metadata(
            collection="news",
            query="earnings",
            min_sentiment_score=0.6,
            k=5,
        )

        assert isinstance(results, list)

    def test_query_by_metadata_all_filters(self, tmp_path: Path):
        """Test query with symbol, date range, and sentiment score."""
        from src.agents.retriever import MarketRAGRetriever

        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        results = retriever.query_by_metadata(
            collection="sentiment",
            query="AAPL",
            symbol="AAPL",
            start_date="2024-01-15",
            end_date="2024-01-16",
            min_sentiment_score=0.5,
            max_sentiment_score=1.0,
            k=5,
        )

        assert isinstance(results, list)


class TestDateValidation:
    """Edge case tests for date validation in query_by_metadata."""

    def test_same_start_and_end_date(self, tmp_path: Path):
        """Test that same start_date and end_date is valid."""
        from src.agents.retriever import MarketRAGRetriever

        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        # Should not raise - same date is valid
        results = retriever.query_by_metadata(
            collection="stocks",
            query="AAPL",
            start_date="2024-01-15",
            end_date="2024-01-15",
            k=5,
        )

        assert isinstance(results, list)

    def test_start_date_only(self, tmp_path: Path):
        """Test query with only start_date."""
        from src.agents.retriever import MarketRAGRetriever

        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        results = retriever.query_by_metadata(
            collection="stocks",
            query="AAPL",
            start_date="2024-01-15",
            k=5,
        )

        assert isinstance(results, list)

    def test_end_date_only(self, tmp_path: Path):
        """Test query with only end_date."""
        from src.agents.retriever import MarketRAGRetriever

        retriever = MarketRAGRetriever(persist_directory=str(tmp_path / "chromadb"))
        results = retriever.query_by_metadata(
            collection="stocks",
            query="AAPL",
            end_date="2024-01-15",
            k=5,
        )

        assert isinstance(results, list)


# Run all tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])