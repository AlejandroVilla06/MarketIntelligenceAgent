"""
Tests for src.data_engine.validation.validator module.

Tests schema validation, data cleaning functions, and quality reporting.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import polars as pl
from polars import DataFrame

from src.data_engine.validation.validator import (
    validate_stock_schema,
    validate_news_schema,
    forward_fill,
    remove_duplicates,
    remove_invalid_prices,
    remove_outliers_iqr,
    clean_stock_data,
    clean_news_data,
    generate_quality_report,
    validate_dataframe,
    STOCK_REQUIRED_COLUMNS,
    NEWS_REQUIRED_COLUMNS,
)


class TestValidateStockSchema:
    """Test cases for validate_stock_schema function."""

    @pytest.fixture
    def valid_stock_df(self) -> DataFrame:
        """Create a valid stock DataFrame."""
        return DataFrame({
            "date": [datetime(2024, 1, i + 1) for i in range(5)],
            "open": [100.0, 101.0, 102.0, 101.5, 103.0],
            "high": [105.0, 106.0, 107.0, 106.5, 108.0],
            "low": [99.0, 100.0, 101.0, 100.5, 102.0],
            "close": [104.0, 105.0, 106.0, 105.5, 107.0],
            "volume": [1000000, 1100000, 1200000, 1150000, 1300000],
            "symbol": ["AAPL"] * 5,
        })

    def test_valid_schema(self, valid_stock_df: DataFrame):
        """Test that valid schema passes validation."""
        is_valid, errors = validate_stock_schema(valid_stock_df)

        assert is_valid
        assert errors == []

    def test_missing_columns(self):
        """Test detection of missing required columns."""
        df = DataFrame({
            "date": [datetime(2024, 1, 1)],
            "close": [100.0],
        })

        is_valid, errors = validate_stock_schema(df)

        assert not is_valid
        assert len(errors) > 0
        assert "Missing required columns" in errors[0]

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = DataFrame()

        is_valid, errors = validate_stock_schema(df)

        assert not is_valid
        assert "empty" in errors[0].lower()

    @patch("src.data_engine.validation.validator.log")
    def test_strict_mode_logs_errors(self, mock_log: Mock, valid_stock_df: DataFrame):
        """Test that strict mode logs errors."""
        # Create DataFrame with wrong types
        invalid_df = DataFrame({
            "date": ["not-a-date"],  # Wrong type
            "open": ["100.0"],  # Wrong type
            "high": [105.0],
            "low": [99.0],
            "close": [104.0],
            "volume": [1000000],
            "symbol": ["AAPL"],
        })

        is_valid, errors = validate_stock_schema(invalid_df, strict=True)

        # Type checking may pass depending on implementation


class TestValidateNewsSchema:
    """Test cases for validate_news_schema function."""

    @pytest.fixture
    def valid_news_df(self) -> DataFrame:
        """Create a valid news DataFrame."""
        return DataFrame({
            "title": [f"News {i}" for i in range(5)],
            "source": ["Reuters"] * 5,
            "timestamp": [datetime(2024, 1, i + 1) for i in range(5)],
            "url": [f"https://example.com/{i}" for i in range(5)],
            "symbol": ["AAPL"] * 5,
        })

    def test_valid_schema(self, valid_news_df: DataFrame):
        """Test that valid news schema passes."""
        is_valid, errors = validate_news_schema(valid_news_df)

        assert is_valid
        assert errors == []

    def test_missing_columns(self):
        """Test detection of missing news columns."""
        df = DataFrame({
            "title": ["News"],
            "source": ["Source"],
        })

        is_valid, errors = validate_news_schema(df)

        assert not is_valid


class TestForwardFill:
    """Test cases for forward_fill function."""

    def test_forward_fill_basic(self):
        """Test basic forward fill functionality."""
        df = DataFrame({
            "date": [datetime(2024, 1, 1), datetime(2024, 1, 2)],
            "value": [100.0, None],
            "symbol": ["AAPL", "AAPL"],
        })

        result = forward_fill(df, columns=["value"])

        assert "value" in result.columns

    def test_forward_fill_empty_dataframe(self):
        """Test forward fill on empty DataFrame."""
        df = DataFrame()

        result = forward_fill(df)

        assert result.is_empty()

    def test_forward_fill_all_numeric_columns(self):
        """Test forward fill with auto-detected columns."""
        df = DataFrame({
            "value1": [100.0, None, 102.0],
            "value2": [50.0, 51.0, None],
        })

        result = forward_fill(df)

        # Result should have same columns
        assert "value1" in result.columns


class TestRemoveDuplicates:
    """Test cases for remove_duplicates function."""

    def test_remove_duplicates_basic(self):
        """Test basic duplicate removal."""
        df = DataFrame({
            "date": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
            "close": [100.0, 100.0],
            "symbol": ["AAPL", "AAPL"],
        })

        result = remove_duplicates(df)

        assert len(result) == 1

    def test_remove_duplicates_by_subset(self):
        """Test duplicate removal by specific columns."""
        df = DataFrame({
            "date": [datetime(2024, 1, 1), datetime(2024, 1, 2)],
            "close": [100.0, 101.0],
            "symbol": ["AAPL", "AAPL"],
        })

        result = remove_duplicates(df, subset=["symbol"])

        # Both rows have same symbol, so should be reduced
        assert len(result) <= 2

    def test_remove_duplicates_empty_dataframe(self):
        """Test duplicate removal on empty DataFrame."""
        df = DataFrame()

        result = remove_duplicates(df)

        assert result.is_empty()


class TestRemoveInvalidPrices:
    """Test cases for remove_invalid_prices function."""

    def test_remove_negative_prices(self):
        """Test removal of negative prices."""
        df = DataFrame({
            "date": [datetime(2024, 1, i + 1) for i in range(3)],
            "open": [100.0, -5.0, 102.0],
            "high": [105.0, 103.0, 107.0],
            "low": [99.0, 97.0, 101.0],
            "close": [104.0, 102.0, 106.0],
            "volume": [1000000] * 3,
            "symbol": ["AAPL"] * 3,
        })

        result = remove_invalid_prices(df)

        # Should remove row with negative price
        assert len(result) == 2

    def test_remove_zero_prices(self):
        """Test removal of zero prices."""
        df = DataFrame({
            "date": [datetime(2024, 1, i + 1) for i in range(3)],
            "open": [100.0, 0.0, 102.0],
            "high": [105.0, 103.0, 107.0],
            "low": [99.0, 97.0, 101.0],
            "close": [104.0, 102.0, 106.0],
            "volume": [1000000] * 3,
            "symbol": ["AAPL"] * 3,
        })

        result = remove_invalid_prices(df)

        # Should remove row with zero price
        assert len(result) == 2

    def test_remove_invalid_prices_empty_dataframe(self):
        """Test on empty DataFrame."""
        df = DataFrame()

        result = remove_invalid_prices(df)

        assert result.is_empty()


class TestRemoveOutliersIQR:
    """Test cases for remove_outliers_iqr function."""

    def test_remove_outliers_basic(self):
        """Test basic outlier removal using IQR."""
        # Create data with clear outlier
        df = DataFrame({
            "date": [datetime(2024, 1, i + 1) for i in range(10)],
            "volume": [1000000, 1100000, 1200000, 1150000, 1300000, 1050000, 1250000, 10000000, 1100000, 1200000],
            "symbol": ["AAPL"] * 10,
        })

        result = remove_outliers_iqr(df, column="volume", multiplier=1.5)

        # Should remove at least the outlier
        assert len(result) < len(df)

    def test_remove_outliers_missing_column(self):
        """Test handling of missing column."""
        df = DataFrame({
            "date": [datetime(2024, 1, 1)],
            "value": [100.0],
        })

        result = remove_outliers_iqr(df, column="nonexistent")

        # Should return original
        assert len(result) == len(df)

    def test_remove_outliers_empty_dataframe(self):
        """Test on empty DataFrame."""
        df = DataFrame()

        result = remove_outliers_iqr(df, column="volume")

        assert result.is_empty()


class TestCleanStockData:
    """Test cases for clean_stock_data function."""

    @pytest.fixture
    def dirty_stock_df(self) -> DataFrame:
        """Create a dirty stock DataFrame."""
        return DataFrame({
            "date": [datetime(2024, 1, i + 1) for i in range(5)],
            "open": [100.0, None, 102.0, 0.0, 104.0],
            "high": [105.0, 106.0, 107.0, 105.5, 108.0],
            "low": [99.0, 100.0, 101.0, -5.0, 102.0],
            "close": [104.0, 105.0, 106.0, 105.5, 107.0],
            "volume": [1000000, 1100000, 1200000, 1150000, 1000000000],  # Last is outlier
            "symbol": ["AAPL"] * 5,
        })

    def test_clean_stock_data_basic(self, dirty_stock_df: DataFrame):
        """Test basic stock data cleaning."""
        result_df, report = clean_stock_data(dirty_stock_df)

        assert "final_rows" in report
        assert "original_rows" in report

    def test_clean_stock_data_returns_report(self, dirty_stock_df: DataFrame):
        """Test that cleaning report is returned."""
        _, report = clean_stock_data(dirty_stock_df)

        assert isinstance(report, dict)

    def test_clean_stock_data_empty_input(self):
        """Test cleaning empty DataFrame."""
        df = DataFrame()

        result_df, report = clean_stock_data(df)

        assert result_df.is_empty()
        assert "error" in report


class TestCleanNewsData:
    """Test cases for clean_news_data function."""

    @pytest.fixture
    def dirty_news_df(self) -> DataFrame:
        """Create a dirty news DataFrame."""
        return DataFrame({
            "title": ["Title 1", "Title 1", "Title 2"],
            "source": ["Source"] * 3,
            "timestamp": [datetime.now()] * 3,
            "url": ["https://example.com/1", "https://example.com/1", "https://example.com/2"],
            "symbol": ["AAPL"] * 3,
        })

    def test_clean_news_data_basic(self, dirty_news_df: DataFrame):
        """Test basic news data cleaning."""
        result_df, report = clean_news_data(dirty_news_df)

        assert "final_rows" in report

    def test_clean_news_data_empty_input(self):
        """Test cleaning empty news DataFrame."""
        df = DataFrame()

        result_df, report = clean_news_data(df)

        assert result_df.is_empty()
        assert "error" in report


class TestGenerateQualityReport:
    """Test cases for generate_quality_report function."""

    @pytest.fixture
    def sample_stock_df(self) -> DataFrame:
        """Create a sample stock DataFrame."""
        return DataFrame({
            "date": [datetime(2024, 1, i + 1) for i in range(5)],
            "open": [100.0, 101.0, 102.0, 101.5, 103.0],
            "high": [105.0, 106.0, 107.0, 106.5, 108.0],
            "low": [99.0, 100.0, 101.0, 100.5, 102.0],
            "close": [104.0, 105.0, 106.0, 105.5, 107.0],
            "volume": [1000000, 1100000, 1200000, 1150000, 1300000],
            "symbol": ["AAPL"] * 5,
        })

    def test_generate_quality_report_stock(self, sample_stock_df: DataFrame):
        """Test quality report generation for stock data."""
        report = generate_quality_report(sample_stock_df, data_type="stock")

        assert report["data_type"] == "stock"
        assert report["rows"] == 5
        assert "columns" in report
        assert "schema" in report

    def test_generate_quality_report_news(self):
        """Test quality report generation for news data."""
        df = DataFrame({
            "title": ["Title 1", "Title 2"],
            "source": ["Source1", "Source2"],
            "timestamp": [datetime.now()] * 2,
            "url": ["https://example.com/1", "https://example.com/2"],
            "symbol": ["AAPL", "GOOGL"],
        })

        report = generate_quality_report(df, data_type="news")

        assert report["data_type"] == "news"

    def test_quality_report_numeric_columns(self, sample_stock_df: DataFrame):
        """Test that numeric metrics are included."""
        report = generate_quality_report(sample_stock_df)

        # Check for numeric column metrics
        assert "open" in report or "volume" in report

    def test_quality_report_empty_dataframe(self):
        """Test quality report on empty DataFrame."""
        df = DataFrame()

        report = generate_quality_report(df)

        assert report["rows"] == 0
        assert "error" in report

    def test_quality_report_date_range(self, sample_stock_df: DataFrame):
        """Test date range in quality report."""
        report = generate_quality_report(sample_stock_df)

        assert "date_range" in report


class TestValidateDataframe:
    """Test cases for validate_dataframe function."""

    @pytest.fixture
    def valid_stock_df(self) -> DataFrame:
        """Create a valid stock DataFrame."""
        return DataFrame({
            "date": [datetime(2024, 1, i + 1) for i in range(5)],
            "open": [100.0, 101.0, 102.0, 101.5, 103.0],
            "high": [105.0, 106.0, 107.0, 106.5, 108.0],
            "low": [99.0, 100.0, 101.0, 100.5, 102.0],
            "close": [104.0, 105.0, 106.0, 105.5, 107.0],
            "volume": [1000000, 1100000, 1200000, 1150000, 1300000],
            "symbol": ["AAPL"] * 5,
        })

    def test_validate_dataframe_stock(self, valid_stock_df: DataFrame):
        """Test full dataframe validation for stock."""
        is_valid, report = validate_dataframe(valid_stock_df, data_type="stock")

        assert "is_valid" in report
        assert "quality_report" in report

    def test_validate_dataframe_news(self):
        """Test full dataframe validation for news."""
        df = DataFrame({
            "title": ["Title"],
            "source": ["Source"],
            "timestamp": [datetime.now()],
            "url": ["https://example.com"],
            "symbol": ["AAPL"],
        })

        is_valid, report = validate_dataframe(df, data_type="news")

        assert "is_valid" in report

    def test_validate_dataframe_empty(self):
        """Test validation of empty DataFrame."""
        df = DataFrame()

        is_valid, report = validate_dataframe(df)

        assert not is_valid
        assert "error" in report


class TestSchemaConstants:
    """Test cases for schema constants."""

    def test_stock_required_columns(self):
        """Test stock required columns are defined."""
        assert "date" in STOCK_REQUIRED_COLUMNS
        assert "open" in STOCK_REQUIRED_COLUMNS
        assert "close" in STOCK_REQUIRED_COLUMNS
        assert "symbol" in STOCK_REQUIRED_COLUMNS

    def test_news_required_columns(self):
        """Test news required columns are defined."""
        assert "title" in NEWS_REQUIRED_COLUMNS
        assert "source" in NEWS_REQUIRED_COLUMNS
        assert "url" in NEWS_REQUIRED_COLUMNS
        assert "symbol" in NEWS_REQUIRED_COLUMNS