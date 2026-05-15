"""
Tests for src.utils module.

Tests formatting utilities and date helpers.
"""

import pytest
from datetime import date, datetime

from src.utils.formatters import (
    format_currency,
    format_percentage,
    format_volume,
    format_timestamp,
    format_value,
)
from src.utils.dates import (
    parse_date,
    date_range,
    trading_days_between,
    is_trading_day,
)


class TestFormatCurrency:
    """Test cases for format_currency function."""

    def test_basic_currency(self):
        """Test basic currency formatting."""
        assert format_currency(1234.56) == "$1,234.56"

    def test_custom_symbol(self):
        """Test currency with custom symbol."""
        assert format_currency(100.0, symbol="€") == "€100.00"

    def test_custom_decimals(self):
        """Test currency with custom decimal places."""
        assert format_currency(0.0523, decimals=4) == "$0.0523"

    def test_none_value(self):
        """Test None handling."""
        assert format_currency(None) == "$—"

    def test_integer_value(self):
        """Test integer values."""
        assert format_currency(1000) == "$1,000.00"


class TestFormatPercentage:
    """Test cases for format_percentage function."""

    def test_basic_percentage(self):
        """Test basic percentage formatting."""
        assert format_percentage(0.0523) == "+5.23%"

    def test_negative_percentage(self):
        """Test negative percentage."""
        assert format_percentage(-0.0312, include_sign=False) == "-3.12%"

    def test_none_value(self):
        """Test None handling."""
        assert format_percentage(None) == "—%"

    def test_zero_value(self):
        """Test zero percentage."""
        assert format_percentage(0.0) == "+0.00%"


class TestFormatVolume:
    """Test cases for format_volume function."""

    def test_thousands(self):
        """Test thousands (K) formatting."""
        assert format_volume(1234) == "1.23K"

    def test_millions(self):
        """Test millions (M) formatting."""
        assert format_volume(1234567) == "1.23M"

    def test_billions(self):
        """Test billions (B) formatting."""
        assert format_volume(1234567890) == "1.23B"

    def test_small_value(self):
        """Test values less than 1000."""
        assert format_volume(999) == "999"

    def test_none_value(self):
        """Test None handling."""
        assert format_volume(None) == "—"


class TestFormatTimestamp:
    """Test cases for format_timestamp function."""

    def test_datetime_object(self):
        """Test datetime object formatting."""
        result = format_timestamp(datetime(2024, 1, 15, 10, 30))
        assert result == "2024-01-15 10:30"

    def test_iso_string(self):
        """Test ISO date string parsing."""
        result = format_timestamp("2024-01-15T10:30:00")
        assert "2024-01-15" in result

    def test_date_only(self):
        """Test date-only formatting."""
        result = format_timestamp("2024-01-15", include_time=False)
        assert result == "2024-01-15"

    def test_none_value(self):
        """Test None handling."""
        assert format_timestamp(None) == "—"


class TestParseDate:
    """Test cases for parse_date function."""

    def test_iso_string(self):
        """Test ISO format date string."""
        result = parse_date("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_us_format(self):
        """Test US format date string."""
        result = parse_date("01/15/2024")
        assert result == date(2024, 1, 15)

    def test_date_object(self):
        """Test date object passthrough."""
        test_date = date(2024, 1, 15)
        result = parse_date(test_date)
        assert result == test_date

    def test_datetime_object(self):
        """Test datetime object conversion."""
        test_dt = datetime(2024, 1, 15, 10, 30)
        result = parse_date(test_dt)
        assert result == date(2024, 1, 15)

    def test_none_value(self):
        """Test None returns None."""
        assert parse_date(None) is None

    def test_invalid_string(self):
        """Test invalid string returns None."""
        assert parse_date("not-a-date") is None


class TestTradingDaysBetween:
    """Test cases for trading_days_between function."""

    def test_weekdays_only(self):
        """Test that only weekdays are counted."""
        # Monday to Friday = 5 trading days
        result = trading_days_between("2024-01-08", "2024-01-12")
        assert result == 5

    def test_includes_weekend(self):
        """Test counting across a weekend."""
        # Monday to next Monday = 7 calendar days, 5 trading days
        result = trading_days_between("2024-01-08", "2024-01-15")
        assert result == 6

    def test_single_day(self):
        """Test single day returns 1."""
        result = trading_days_between("2024-01-15", "2024-01-15")
        assert result == 1

    def test_reversed_dates(self):
        """Test that dates can be in any order."""
        result = trading_days_between("2024-01-15", "2024-01-08")
        assert result == 6


class TestIsTradingDay:
    """Test cases for is_trading_day function."""

    def test_weekday(self):
        """Test that regular weekdays are trading days."""
        # Monday Jan 15, 2024
        assert is_trading_day("2024-01-15") is True

    def test_weekend(self):
        """Test that weekends are not trading days."""
        # Saturday Jan 13, 2024
        assert is_trading_day("2024-01-13") is False

    def test_new_years_day(self):
        """Test that major holidays are not trading days."""
        # Jan 1, 2024 (Monday)
        assert is_trading_day("2024-01-01") is False

    def test_christmas(self):
        """Test Christmas is not a trading day."""
        # Dec 25, 2024 (Wednesday)
        assert is_trading_day("2024-12-25") is False

    def test_none_value(self):
        """Test None returns False."""
        assert is_trading_day(None) is False


class TestFormatValue:
    """Test cases for format_value function."""

    def test_auto_currency(self):
        """Test auto formatting for normal currency values."""
        result = format_value(1234.56)
        assert "$" in result

    def test_auto_percentage(self):
        """Test auto formatting for small values."""
        result = format_value(0.05)
        assert "%" in result

    def test_auto_volume(self):
        """Test auto formatting for large values."""
        result = format_value(1500000)
        assert "M" in result

    def test_currency_style(self):
        """Test explicit currency style."""
        result = format_value(100.50, style="currency")
        assert result == "$100.50"

    def test_percentage_style(self):
        """Test explicit percentage style."""
        result = format_value(0.25, style="percentage")
        assert result == "+25.00%"

    def test_volume_style(self):
        """Test explicit volume style."""
        result = format_value(5000, style="volume")
        assert result == "5.00K"

    def test_none_value(self):
        """Test None handling."""
        assert format_value(None) == "—"

    def test_string_passthrough(self):
        """Test string values are returned as-is."""
        assert format_value("test") == "test"