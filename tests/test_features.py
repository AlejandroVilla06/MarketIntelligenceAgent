"""
Tests for src.ml_models.features.indicators module.

Tests all technical indicator functions: SMA, EMA, RSI, MACD,
Bollinger Bands, and volume features.
"""

import pytest
import warnings
from datetime import datetime

import polars as pl
from polars import DataFrame

from src.ml_models.features.indicators import (
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
    calculate_volume_features,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def stock_df() -> DataFrame:
    """Create a sample stock DataFrame for testing."""
    dates = [datetime(2024, 1, i + 1) for i in range(30)]
    # Create realistic price data with an uptrend
    close_prices = [100.0 + i * 0.5 + (i % 3) * 0.2 for i in range(30)]
    return DataFrame({
        "date": dates,
        "open": [p * 0.99 for p in close_prices],
        "high": [p * 1.02 for p in close_prices],
        "low": [p * 0.98 for p in close_prices],
        "close": close_prices,
        "volume": [1000000 + i * 10000 for i in range(30)],
    })


@pytest.fixture
def insufficient_data_df() -> DataFrame:
    """Create a DataFrame with insufficient data for indicator calculations."""
    return DataFrame({
        "date": [datetime(2024, 1, 1), datetime(2024, 1, 2)],
        "close": [100.0, 101.0],
        "volume": [1000000, 1100000],
    })


# =============================================================================
# TEST CALCULATE_SMA
# =============================================================================


class TestCalculateSMA:
    """Test cases for calculate_sma function."""

    def test_sma_with_valid_data(self, stock_df: DataFrame):
        """Test SMA calculation with valid data."""
        result = calculate_sma(stock_df, "close", period=5)

        assert result.len() == 30
        assert result.name == "sma_5"
        # First 4 values should be null (not enough data)
        assert result[0] is None
        assert result[1] is None
        assert result[2] is None
        assert result[3] is None
        # 5th value should be the mean of first 5 close prices
        assert result[4] is not None

    def test_sma_with_different_periods(self, stock_df: DataFrame):
        """Test SMA with different period values."""
        result_10 = calculate_sma(stock_df, "close", period=10)
        result_20 = calculate_sma(stock_df, "close", period=20)

        assert result_10.name == "sma_10"
        assert result_20.name == "sma_20"
        assert result_20.len() == 30

    def test_sma_with_invalid_column(self, stock_df: DataFrame):
        """Test SMA with non-existent column returns empty series."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = calculate_sma(stock_df, "invalid_column", period=5)

            assert result.len() == 1
            assert result.name == "sma_5"
            assert len(w) > 0

    def test_sma_with_insufficient_data(self, insufficient_data_df: DataFrame):
        """Test SMA with insufficient data."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = calculate_sma(insufficient_data_df, "close", period=20)

            assert result[0] is None
            assert len(w) > 0

    def test_sma_with_negative_period(self, stock_df: DataFrame):
        """Test SMA with negative period uses absolute value."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = calculate_sma(stock_df, "close", period=-10)

            assert result.name == "sma_10"
            assert len(w) > 0


# =============================================================================
# TEST CALCULATE_EMA
# =============================================================================


class TestCalculateEMA:
    """Test cases for calculate_ema function."""

    def test_ema_with_valid_data(self, stock_df: DataFrame):
        """Test EMA calculation with valid data."""
        result = calculate_ema(stock_df, "close", period=5)

        assert result.len() == 30
        assert result.name == "ema_5"

    def test_ema_with_different_periods(self, stock_df: DataFrame):
        """Test EMA with different period values."""
        result_12 = calculate_ema(stock_df, "close", period=12)
        result_26 = calculate_ema(stock_df, "close", period=26)

        assert result_12.name == "ema_12"
        assert result_26.name == "ema_26"
        assert result_26.len() == 30

    def test_ema_with_invalid_column(self, stock_df: DataFrame):
        """Test EMA with non-existent column."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = calculate_ema(stock_df, "invalid_column", period=5)

            assert result.len() == 1
            assert result.name == "ema_5"
            assert len(w) > 0


# =============================================================================
# TEST CALCULATE_RSI
# =============================================================================


class TestCalculateRSI:
    """Test cases for calculate_rsi function."""

    def test_rsi_with_valid_data(self, stock_df: DataFrame):
        """Test RSI calculation with valid data."""
        result = calculate_rsi(stock_df, "close", period=14)

        assert result.len() == 30
        assert result.name == "rsi_14"

    def test_rsi_values_in_range(self, stock_df: DataFrame):
        """Test RSI values are in 0-100 range."""
        result = calculate_rsi(stock_df, "close", period=14)

        # Check non-null values are in valid range
        non_null_values = [v for v in result.to_list() if v is not None]
        for val in non_null_values:
            assert 0.0 <= val <= 100.0, f"RSI value {val} out of range"

    def test_rsi_with_default_period(self, stock_df: DataFrame):
        """Test RSI with default period (14)."""
        result = calculate_rsi(stock_df, "close")

        assert result.name == "rsi_14"

    def test_rsi_with_invalid_column(self, stock_df: DataFrame):
        """Test RSI with non-existent column."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = calculate_rsi(stock_df, "invalid_column", period=14)

            assert result.len() == 1
            assert result.name == "rsi_14"
            assert len(w) > 0


# =============================================================================
# TEST CALCULATE_MACD
# =============================================================================


class TestCalculateMACD:
    """Test cases for calculate_macd function."""

    def test_macd_with_valid_data(self, stock_df: DataFrame):
        """Test MACD calculation with valid data."""
        result = calculate_macd(stock_df, "close", fast_period=12, slow_period=26)

        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result

        # Check names
        assert result["macd"].name == "macd_12_26"
        assert result["signal"].name == "macd_signal_9"
        assert result["histogram"].name == "macd_hist_12_26"

    def test_macd_with_custom_periods(self, stock_df: DataFrame):
        """Test MACD with custom periods."""
        result = calculate_macd(
            stock_df,
            "close",
            fast_period=5,
            slow_period=15,
            signal_period=5,
        )

        assert result["macd"].name == "macd_5_15"
        assert result["signal"].name == "macd_signal_5"
        assert result["histogram"].name == "macd_hist_5_15"

    def test_macd_slow_less_than_fast(self, stock_df: DataFrame):
        """Test MACD when slow_period < fast_period swaps values."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Slow period less than fast period (invalid)
            result = calculate_macd(
                stock_df,
                "close",
                fast_period=26,
                slow_period=12,
            )

            # Should swap and use 12 as fast, 26 as slow
            assert result["macd"].name == "macd_12_26"
            assert len(w) > 0

    def test_macd_with_invalid_column(self, stock_df: DataFrame):
        """Test MACD with non-existent column."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            calculate_macd(stock_df, "invalid_col")

            # All series should be empty or have single element
            assert len(w) > 0


# =============================================================================
# TEST CALCULATE_BOLLINGER_BANDS
# =============================================================================


class TestCalculateBollingerBands:
    """Test cases for calculate_bollinger_bands function."""

    def test_bb_with_valid_data(self, stock_df: DataFrame):
        """Test Bollinger Bands calculation."""
        result = calculate_bollinger_bands(stock_df, "close", period=20)

        assert "upper" in result
        assert "middle" in result
        assert "lower" in result

        # Check names
        assert result["upper"].name == "bb_upper_20"
        assert result["middle"].name == "bb_middle_20"
        assert result["lower"].name == "bb_lower_20"

    def test_bb_upper_greater_than_middle(self, stock_df: DataFrame):
        """Test that upper band > middle band > lower band."""
        result = calculate_bollinger_bands(stock_df, "close", period=10)

        upper = result["upper"].to_list()
        middle = result["middle"].to_list()
        lower = result["lower"].to_list()

        # Check valid triples
        for i in range(len(upper)):
            if upper[i] is not None and middle[i] is not None and lower[i] is not None:
                assert upper[i] > middle[i], f"Upper[{i}] should > middle[{i}]"
                assert middle[i] > lower[i], f"Middle[{i}] should > lower[{i}]"

    def test_bb_with_custom_std(self, stock_df: DataFrame):
        """Test Bollinger Bands with custom standard deviation."""
        result_1 = calculate_bollinger_bands(stock_df, "close", period=20, num_std=1.0)
        result_2 = calculate_bollinger_bands(stock_df, "close", period=20, num_std=2.0)

        # Bands with 1 std should be narrower
        upper_1 = result_1["upper"].to_list()
        lower_1 = result_1["lower"].to_list()
        upper_2 = result_2["upper"].to_list()
        lower_2 = result_2["lower"].to_list()

        for i in range(len(upper_1)):
            if (upper_1[i] is not None and upper_2[i] is not None and
                    upper_1[i] is not None and upper_2[i] is not None):
                # With larger std, band should be wider
                width_1 = upper_1[i] - lower_1[i]
                width_2 = upper_2[i] - lower_2[i]
                assert width_2 > width_1

    def test_bb_with_invalid_column(self, stock_df: DataFrame):
        """Test Bollinger Bands with non-existent column."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            calculate_bollinger_bands(stock_df, "invalid_col")

            assert len(w) > 0


# =============================================================================
# TEST CALCULATE_VOLUME_FEATURES
# =============================================================================


class TestCalculateVolumeFeatures:
    """Test cases for calculate_volume_features function."""

    def test_volume_with_valid_data(self, stock_df: DataFrame):
        """Test volume features calculation."""
        result = calculate_volume_features(stock_df, "volume", period=20)

        assert "volume_sma" in result
        assert "volume_ratio" in result

        # Check names
        assert result["volume_sma"].name == "volume_sma_20"
        assert result["volume_ratio"].name == "volume_ratio_20"

    def test_volume_ratio_around_one(self, stock_df: DataFrame):
        """Test volume ratio is around 1 when constant volume."""
        # Create df with constant volume
        const_vol_df = stock_df.with_columns([
            pl.lit(1000000).alias("volume"),
        ])

        result = calculate_volume_features(const_vol_df, "volume", period=10)

        # After initial warmup, ratio should be around 1
        ratio = result["volume_ratio"].to_list()
        # Filter nulls and check last values
        valid_ratios = [r for r in ratio[15:] if r is not None]
        for r in valid_ratios:
            assert 0.5 < r < 2.0, f"Volume ratio {r} out of expected range"

    def test_volume_with_default_period(self, stock_df: DataFrame):
        """Test volume features with default period."""
        result = calculate_volume_features(stock_df, "volume")

        assert result["volume_sma"].name == "volume_sma_20"

    def test_volume_with_invalid_column(self, stock_df: DataFrame):
        """Test volume features with non-existent column."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            calculate_volume_features(stock_df, "invalid_col")

            assert len(w) > 0


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test functions with empty DataFrame."""
        empty_df = DataFrame()

        # Should handle gracefully without crashing
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            sma_result = calculate_sma(empty_df, "close", 5)
            ema_result = calculate_ema(empty_df, "close", 5)

            assert sma_result.len() <= 1
            assert ema_result.len() <= 1

    def test_zero_period(self, stock_df: DataFrame):
        """Test functions with zero period."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            result = calculate_sma(stock_df, "close", 0)

            # Should use absolute value (1)
            assert result.name == "sma_1"
            assert len(w) > 0

    def test_all_zero_prices(self):
        """Test with all zero prices."""
        df = DataFrame({
            "date": [datetime(2024, 1, i + 1) for i in range(20)],
            "close": [0.0] * 20,
            "volume": [1000000] * 20,
        })

        # Should not crash, may return NaN/null values
        result = calculate_sma(df, "close", 10)
        assert result.len() == 20