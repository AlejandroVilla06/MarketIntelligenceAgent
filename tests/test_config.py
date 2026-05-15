"""
Tests for src.config module.
"""

import pytest
from src.config import Settings


class TestSettings:
    """Test cases for Settings class."""

    def test_tracked_symbols_parse(self):
        """Test that comma-separated symbols are parsed correctly."""
        s = Settings(tracked_symbols="AAPL,GOOGL,NVDA")
        assert s.tracked_symbols == ["AAPL", "GOOGL", "NVDA"]

    def test_tracked_symbols_uppercase(self):
        """Test that symbols are converted to uppercase."""
        s = Settings(tracked_symbols="aapl,googl")
        assert s.tracked_symbols == ["AAPL", "GOOGL"]

    def test_data_refresh_interval_bounds(self):
        """Test that refresh interval is bounded."""
        s = Settings(data_refresh_interval=30)
        assert s.data_refresh_interval == 30

    def test_data_refresh_interval_valid_range(self):
        """Test that valid refresh intervals are accepted."""
        s_min = Settings(data_refresh_interval=1)
        assert s_min.data_refresh_interval == 1

        s_max = Settings(data_refresh_interval=1440)
        assert s_max.data_refresh_interval == 1440

    def test_default_tracked_symbols(self):
        """Test that default symbols are used when not provided."""
        s = Settings()
        assert "AAPL" in s.tracked_symbols
        assert "GOOGL" in s.tracked_symbols

    def test_empty_symbol_string(self):
        """Test handling of empty or whitespace-only symbol strings."""
        s = Settings(tracked_symbols="   ")
        assert s.tracked_symbols == []

    def test_symbols_with_whitespace(self):
        """Test that symbols with extra whitespace are trimmed."""
        s = Settings(tracked_symbols="  AAPL  ,  GOOGL  , NVDA ")
        assert s.tracked_symbols == ["AAPL", "GOOGL", "NVDA"]