"""
Tests for src.data_engine.storage module.

Tests the StorageInterface class for Parquet read/write operations
and partitioning functionality.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import polars as pl
from polars import DataFrame

from src.data_engine.storage import StorageInterface


class TestStorageInterface:
    """Test cases for StorageInterface class."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> StorageInterface:
        """Create a StorageInterface instance with temporary directory."""
        return StorageInterface(base_dir=tmp_path)

    @pytest.fixture
    def sample_stock_df(self) -> DataFrame:
        """Create a sample stock DataFrame for testing."""
        dates = [datetime(2024, 1, i + 1) for i in range(5)]
        return DataFrame({
            "date": dates,
            "open": [100.0, 101.0, 102.0, 101.5, 103.0],
            "high": [105.0, 106.0, 107.0, 106.5, 108.0],
            "low": [99.0, 100.0, 101.0, 100.5, 102.0],
            "close": [104.0, 105.0, 106.0, 105.5, 107.0],
            "volume": [1000000, 1100000, 1200000, 1150000, 1300000],
            "symbol": ["AAPL"] * 5,
        })

    @pytest.fixture
    def sample_news_df(self) -> DataFrame:
        """Create a sample news DataFrame for testing."""
        timestamps = [datetime(2024, 1, i + 1) for i in range(5)]
        return DataFrame({
            "title": [f"News title {i}" for i in range(5)],
            "source": ["Reuters"] * 5,
            "timestamp": timestamps,
            "url": [f"https://example.com/{i}" for i in range(5)],
            "symbol": ["AAPL"] * 5,
        })

    # =============================================================================
    # SAVE STOCKS TESTS
    # =============================================================================

    def test_save_stocks_basic(self, temp_storage: StorageInterface, sample_stock_df: DataFrame):
        """Test saving stock data to Parquet file."""
        filepath = temp_storage.save_stocks(sample_stock_df, filename="test_stocks.parquet")

        assert filepath.exists()
        assert filepath.name == "test_stocks.parquet"

    def test_save_stocks_returns_path(self, temp_storage: StorageInterface, sample_stock_df: DataFrame):
        """Test that save_stocks returns the file path."""
        filepath = temp_storage.save_stocks(sample_stock_df)

        assert isinstance(filepath, Path)

    def test_save_stocks_empty_dataframe_raises(self, temp_storage: StorageInterface):
        """Test that saving empty DataFrame raises ValueError."""
        empty_df = DataFrame()

        with pytest.raises(ValueError, match="Cannot save empty"):
            temp_storage.save_stocks(empty_df)

    # =============================================================================
    # LOAD STOCKS TESTS
    # =============================================================================

    def test_load_stocks_basic(self, temp_storage: StorageInterface, sample_stock_df: DataFrame):
        """Test loading stock data from Parquet file."""
        temp_storage.save_stocks(sample_stock_df, filename="test_load.parquet")

        df = temp_storage.load_stocks(filename="test_load.parquet")

        assert len(df) == 5
        assert "symbol" in df.columns

    def test_load_stocks_missing_file_returns_empty(self, temp_storage: StorageInterface):
        """Test that loading non-existent file returns empty DataFrame."""
        df = temp_storage.load_stocks(filename="nonexistent.parquet")

        assert df.is_empty()

    def test_load_stocks_filter_by_symbols(self, temp_storage: StorageInterface):
        """Test loading stocks with symbol filter."""
        dates = [datetime(2024, 1, i + 1) for i in range(3)]
        df = DataFrame({
            "date": dates * 2,
            "open": [100.0] * 6,
            "high": [105.0] * 6,
            "low": [99.0] * 6,
            "close": [104.0] * 6,
            "volume": [1000000] * 6,
            "symbol": ["AAPL", "GOOGL", "MSFT"] * 2,
        })
        temp_storage.save_stocks(df, filename="multi_symbols.parquet")

        result = temp_storage.load_stocks(symbols=["AAPL"], filename="multi_symbols.parquet")

        assert len(result) == 2
        assert set(result.get_column("symbol").to_list()) == {"AAPL"}

    def test_load_stocks_filter_by_date_range(self, temp_storage: StorageInterface):
        """Test loading stocks with date range filter."""
        dates = [datetime(2024, 1, i + 1) for i in range(10)]
        df = DataFrame({
            "date": dates,
            "open": [100.0] * 10,
            "high": [105.0] * 10,
            "low": [99.0] * 10,
            "close": [104.0] * 10,
            "volume": [1000000] * 10,
            "symbol": ["AAPL"] * 10,
        })
        temp_storage.save_stocks(df, filename="date_filter.parquet")

        result = temp_storage.load_stocks(
            start_date=datetime(2024, 1, 5),
            end_date=datetime(2024, 1, 8),
            filename="date_filter.parquet",
        )

        assert len(result) == 4

    def test_load_stocks_string_dates(self, temp_storage: StorageInterface):
        """Test loading stocks with string date filters."""
        dates = [datetime(2024, 1, i + 1) for i in range(5)]
        df = DataFrame({
            "date": dates,
            "open": [100.0] * 5,
            "high": [105.0] * 5,
            "low": [99.0] * 5,
            "close": [104.0] * 5,
            "volume": [1000000] * 5,
            "symbol": ["AAPL"] * 5,
        })
        temp_storage.save_stocks(df, filename="string_dates.parquet")

        result = temp_storage.load_stocks(
            start_date="2024-01-03",
            end_date="2024-01-05",
            filename="string_dates.parquet",
        )

        assert len(result) == 3

    # =============================================================================
    # SAVE NEWS TESTS
    # =============================================================================

    def test_save_news_basic(self, temp_storage: StorageInterface, sample_news_df: DataFrame):
        """Test saving news data to Parquet file."""
        filepath = temp_storage.save_news(sample_news_df, filename="test_news.parquet")

        assert filepath.exists()
        assert filepath.name == "test_news.parquet"

    def test_save_news_empty_dataframe_raises(self, temp_storage: StorageInterface):
        """Test that saving empty news DataFrame raises ValueError."""
        empty_df = DataFrame()

        with pytest.raises(ValueError, match="Cannot save empty"):
            temp_storage.save_news(empty_df)

    # =============================================================================
    # LOAD NEWS TESTS
    # =============================================================================

    def test_load_news_basic(self, temp_storage: StorageInterface, sample_news_df: DataFrame):
        """Test loading news data from Parquet file."""
        temp_storage.save_news(sample_news_df, filename="test_load_news.parquet")

        df = temp_storage.load_news(filename="test_load_news.parquet")

        assert len(df) == 5
        assert "url" in df.columns

    def test_load_news_missing_file_returns_empty(self, temp_storage: StorageInterface):
        """Test that loading non-existent news file returns empty DataFrame."""
        df = temp_storage.load_news(filename="nonexistent_news.parquet")

        assert df.is_empty()

    def test_load_news_filter_by_symbols(self, temp_storage: StorageInterface):
        """Test loading news with symbol filter."""
        timestamps = [datetime(2024, 1, i + 1) for i in range(3)]
        df = DataFrame({
            "title": [f"Title {i}" for i in range(3)],
            "source": ["Reuters"] * 3,
            "timestamp": timestamps,
            "url": [f"https://example.com/{i}" for i in range(3)],
            "symbol": ["AAPL", "GOOGL", "MSFT"],
        })
        temp_storage.save_news(df, filename="filter_news.parquet")

        result = temp_storage.load_news(symbols=["AAPL"], filename="filter_news.parquet")

        assert len(result) == 1

    # =============================================================================
    # LIST TESTS
    # =============================================================================

    def test_list_stocks_returns_files(self, temp_storage: StorageInterface, sample_stock_df: DataFrame):
        """Test listing stock files."""
        temp_storage.save_stocks(sample_stock_df, filename="stock1.parquet")
        temp_storage.save_stocks(sample_stock_df, filename="stock2.parquet")

        files = temp_storage.list_stocks()

        assert len(files) == 2

    def test_list_stocks_empty_directory(self, temp_storage: StorageInterface):
        """Test listing stocks when directory is empty."""
        files = temp_storage.list_stocks()

        assert files == []

    def test_list_news_returns_files(self, temp_storage: StorageInterface, sample_news_df: DataFrame):
        """Test listing news files."""
        temp_storage.save_news(sample_news_df, filename="news1.parquet")

        files = temp_storage.list_news()

        assert len(files) == 1

    # =============================================================================
    # PARTITIONING TESTS
    # =============================================================================

    def test_partition_by_symbol(self, temp_storage: StorageInterface):
        """Test partitioning functionality by symbol column."""
        dates = [datetime(2024, 1, i + 1) for i in range(3)]
        df = DataFrame({
            "date": dates * 2,
            "open": [100.0] * 6,
            "high": [105.0] * 6,
            "low": [99.0] * 6,
            "close": [104.0] * 6,
            "volume": [1000000] * 6,
            "symbol": ["AAPL", "AAPL", "AAPL", "GOOGL", "GOOGL", "GOOGL"],
        })

        # Note: Full partition support would require additional implementation
        # This tests that data can be saved and filtered after
        temp_storage.save_stocks(df, filename="partitioned.parquet")

        aapl_df = temp_storage.load_stocks(symbols=["AAPL"], filename="partitioned.parquet")
        googl_df = temp_storage.load_stocks(symbols=["GOOGL"], filename="partitioned.parquet")

        assert len(aapl_df) == 3
        assert len(googl_df) == 3

    # =============================================================================
    # DIRECTORY CREATION TESTS
    # =============================================================================

    def test_ensure_directories_creates_dirs(self, tmp_path: Path):
        """Test that _ensure_directories creates required directories."""
        test_dir = tmp_path / "new_test_dir"
        storage = StorageInterface(base_dir=test_dir)

        storage._ensure_directories()

        assert test_dir.exists()
        assert (test_dir / "stocks").exists()
        assert (test_dir / "news").exists()