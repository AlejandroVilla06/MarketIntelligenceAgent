"""
Technical Indicators for Stock Market Analysis
============================================

Functions to compute SMA, EMA, RSI, MACD, Bollinger Bands, and volume features.
All functions return Polars Series and work with Polars DataFrames.

Usage:
    from src.ml_models.features import calculate_sma, calculate_rsi
    sma = calculate_sma(df, column="close", period=20)
    rsi = calculate_rsi(df, column="close", period=14)
"""

from __future__ import annotations

import warnings
from typing import TypedDict

import polars as pl
from polars import DataFrame, Series

# =============================================================================
# LOGGING
# =============================================================================

from src.utils import get_logger

logger = get_logger(__name__)


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================


class MACDResult(TypedDict):
    """MACD calculation result."""

    macd: Series
    signal: Series
    histogram: Series


class BollingerBandsResult(TypedDict):
    """Bollinger Bands calculation result."""

    upper: Series
    middle: Series
    lower: Series


class VolumeFeaturesResult(TypedDict):
    """Volume features calculation result."""

    volume_sma: Series
    volume_ratio: Series


# =============================================================================
# SIMPLE MOVING AVERAGE (SMA)
# =============================================================================


def calculate_sma(df: DataFrame, column: str = "close", period: int = 20) -> Series:
    """
    Calculate Simple Moving Average (SMA).

    Computes the arithmetic mean of the last 'period' values for the specified
    column. SMA is commonly used to identify trend direction and support/resistance
    levels.

    Args:
        df: Polars DataFrame with stock data.
        column: Column name to calculate SMA for (default: "close").
        period: Number of periods for moving average (default: 20).

    Returns:
        Polars Series with SMA values named "sma_{period}".

    Examples:
        >>> df = DataFrame({"close": [100, 101, 102, 103, 104]})
        >>> calculate_sma(df, "close", period=3)
        shape: (5,)
        Series: 'sma_3' [None, None, 101.0, 102.0, 103.0]
    """
    if column not in df.columns:
        warnings.warn(
            f"Column '{column}' not found in DataFrame. Returning empty Series."
        )
        return Series(f"sma_{period}", [None])

    if period <= 0:
        warnings.warn(f"Invalid period {period}. Using absolute value.")
        period = max(1, abs(period))

    if df.height < period:
        warnings.warn(
            f"Insufficient data: {df.height} rows for period {period}. "
            f"Need at least {period} data points."
        )
        return Series(f"sma_{period}", [None])

    sma_series = df.get_column(column).rolling_mean(period).rename(f"sma_{period}")

    logger.debug(f"Calculated SMA_{period} for {column}: {sma_series.len()} values")
    return sma_series


# =============================================================================
# EXPONENTIAL MOVING AVERAGE (EMA)
# =============================================================================


def calculate_ema(df: DataFrame, column: str = "close", period: int = 12) -> Series:
    """
    Calculate Exponential Moving Average (EMA).

    Computes the exponentially weighted moving average, giving more weight to recent
    prices. EMA responds more quickly to price changes than SMA.

    Args:
        df: Polars DataFrame with stock data.
        column: Column name to calculate EMA for (default: "close").
        period: Number of periods for EMA (default: 12).

    Returns:
        Polars Series with EMA values named "ema_{period}".

    Examples:
        >>> df = DataFrame({"close": [100, 101, 102, 103, 104]})
        >>> calculate_ema(df, "close", period=3)
        shape: (5,)
        Series: 'ema_3' [None, None, None, 102.666..., 103.44...]
    """
    if column not in df.columns:
        warnings.warn(
            f"Column '{column}' not found in DataFrame. Returning empty Series."
        )
        return Series(f"ema_{period}", [None])

    if period <= 0:
        warnings.warn(f"Invalid period {period}. Using absolute value.")
        period = max(1, abs(period))

    if df.height < period:
        warnings.warn(
            f"Insufficient data: {df.height} rows for period {period}. "
            f"Need at least {period} data points."
        )
        return Series(f"ema_{period}", [None])

    ema_series = df.get_column(column).ewm_mean(span=period).rename(f"ema_{period}")

    logger.debug(f"Calculated EMA_{period} for {column}: {ema_series.len()} values")
    return ema_series


# =============================================================================
# RELATIVE STRENGTH INDEX (RSI)
# =============================================================================


def calculate_rsi(df: DataFrame, column: str = "close", period: int = 14) -> Series:
    """
    Calculate Relative Strength Index (RSI).

    Measures the magnitude and speed of price changes. RSI ranges from 0 to 100,
    where values above 70 indicate overbought conditions and values below 30
    indicate oversold conditions.

    Args:
        df: Polars DataFrame with stock data.
        column: Column name to calculate RSI for (default: "close").
        period: Number of periods for RSI calculation (default: 14).

    Returns:
        Polars Series with RSI values (0-100) named "rsi_{period}".

    Examples:
        >>> df = DataFrame({"close": [100, 101, 102, 103, 104, 105, 106]})
        >>> calculate_rsi(df, "close", period=3)
        shape: (7,)
        Series: 'rsi_3' [None, None, None, 80.0, 85.71..., 90.0, 93.33...]
    """
    if column not in df.columns:
        warnings.warn(
            f"Column '{column}' not found in DataFrame. Returning empty Series."
        )
        return Series(f"rsi_{period}", [None])

    if period <= 0:
        warnings.warn(f"Invalid period {period}. Using absolute value.")
        period = max(1, abs(period))

    if df.height < period + 1:
        warnings.warn(
            f"Insufficient data: {df.height} rows for period {period}. "
            f"Need at least {period + 1} data points."
        )
        return Series(f"rsi_{period}", [None])

    # Calculate price changes (differences)
    price_series = df.get_column(column)
    changes = price_series.diff()

    # Compute gains (positive changes) and losses (negative changes as positive values)
    gains = changes.map_elements(
        lambda x: x if x is not None and x > 0 else 0.0, return_dtype=pl.Float64
    )
    losses = changes.map_elements(
        lambda x: abs(x) if x is not None and x < 0 else 0.0, return_dtype=pl.Float64
    )

    # Calculate average gains and losses using EMA (Wilder's smoothing method)
    avg_gain = pl.Series("avg_gain", gains).ewm_mean(alpha=1.0 / period)
    avg_loss = pl.Series("avg_loss", losses).ewm_mean(alpha=1.0 / period)

    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi_values = rs.map_elements(
        lambda x: (
            100.0 - (100.0 / (1.0 + x))
            if x is not None and x > 0
            else 50.0
            if x == 0
            else 100.0
            if x == float("inf")
            else 0.0
        ),
        return_dtype=pl.Float64,
    )
    rsi_series = pl.Series(f"rsi_{period}", rsi_values)

    logger.debug(f"Calculated RSI_{period} for {column}: {rsi_series.len()} values")
    return rsi_series


# =============================================================================
# MACD (MOVING AVERAGE CONVERGENCE DIVERGENCE)
# =============================================================================


def calculate_macd(
    df: DataFrame,
    column: str = "close",
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> MACDResult:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    MACD is a momentum oscillator that shows the relationship between two
    moving averages of a security's price. It consists of:
    - MACD line: Difference between fast and slow EMA
    - Signal line: EMA of the MACD line
    - Histogram: Difference between MACD line and signal line

    Args:
        df: Polars DataFrame with stock data.
        column: Column name to calculate MACD for (default: "close").
        fast_period: Fast EMA period (default: 12).
        slow_period: Slow EMA period (default: 26).
        signal_period: Signal line EMA period (default: 9).

    Returns:
        Dictionary with keys:
            - "macd": MACD line Series
            - "signal": Signal line Series
            - "histogram": Histogram Series (MACD - signal)

    Examples:
        >>> df = DataFrame({"close": [100, 101, 102, 103, 104] * 6})
        >>> result = calculate_macd(df, fast_period=12, slow_period=26)
        >>> result["macd"]
        shape: (30,)
        Series: 'macd_12_26' [...]
    """
    if column not in df.columns:
        warnings.warn(
            f"Column '{column}' not found in DataFrame. Returning empty result."
        )
        empty_series = Series("macd")
        return {
            "macd": empty_series,
            "signal": empty_series,
            "histogram": empty_series,
        }

    if fast_period <= 0 or slow_period <= 0 or signal_period <= 0:
        warnings.warn("Invalid periods. Using absolute values.")
        fast_period = abs(fast_period)
        slow_period = abs(slow_period)
        signal_period = abs(signal_period)

    if slow_period <= fast_period:
        warnings.warn(
            f"slow_period ({slow_period}) should be > fast_period ({fast_period}). "
            f"Swapping values."
        )
        fast_period, slow_period = slow_period, fast_period

    if df.height < slow_period:
        warnings.warn(
            f"Insufficient data: {df.height} rows. Need at least {slow_period} data points."
        )
        empty_series = Series(f"macd_{fast_period}_{slow_period}")
        return {
            "macd": empty_series,
            "signal": empty_series,
            "histogram": empty_series,
        }

    # Calculate fast and slow EMAs
    fast_ema = calculate_ema(df, column, fast_period)
    slow_ema = calculate_ema(df, column, slow_period)

    # Ensure equal length for subtraction
    fast_ema_list = fast_ema.to_list()
    slow_ema_list = slow_ema.to_list()

    # MACD line = fast EMA - slow EMA
    macd_values = [
        f - s if f is not None and s is not None else None
        for f, s in zip(fast_ema_list, slow_ema_list)
    ]
    macd_series = pl.Series(f"macd_{fast_period}_{slow_period}", macd_values)

    # Signal line = EMA of MACD line (using ewm_mean)
    signal_series = pl.Series(
        f"macd_{fast_period}_{slow_period}", macd_values
    ).ewm_mean(alpha=1.0 / signal_period)
    signal_series = signal_series.rename(f"macd_signal_{signal_period}")

    # Histogram = MACD line - signal line
    macd_list = macd_series.to_list()
    signal_list = signal_series.to_list()
    histogram_values = [
        m - s if m is not None and s is not None else None
        for m, s in zip(macd_list, signal_list)
    ]
    histogram_series = pl.Series(
        f"macd_hist_{fast_period}_{slow_period}", histogram_values
    )

    result: MACDResult = {
        "macd": macd_series,
        "signal": signal_series,
        "histogram": histogram_series,
    }

    logger.debug(
        f"Calculated MACD({fast_period}, {slow_period}, {signal_period}): "
        f"{len(macd_series)} values"
    )
    return result


# =============================================================================
# BOLLINGER BANDS
# =============================================================================


def calculate_bollinger_bands(
    df: DataFrame,
    column: str = "close",
    period: int = 20,
    num_std: float = 2.0,
) -> BollingerBandsResult:
    """
    Calculate Bollinger Bands.

    Bollinger Bands are a technical analysis tool that consists of:
    - Upper band: Middle band + (num_std * standard deviation)
    - Middle band: Simple Moving Average (SMA)
    - Lower band: Middle band - (num_std * standard deviation)

    The bands expand and contract based on market volatility.

    Args:
        df: Polars DataFrame with stock data.
        column: Column name to calculate bands for (default: "close").
        period: Number of periods for SMA and standard deviation (default: 20).
        num_std: Number of standard deviations for bands (default: 2.0).

    Returns:
        Dictionary with keys:
            - "upper": Upper band Series
            - "middle": Middle band (SMA) Series
            - "lower": Lower band Series

    Examples:
        >>> df = DataFrame({"close": [100, 101, 102, 103, 104] * 5})
        >>> result = calculate_bollinger_bands(df, period=20, num_std=2.0)
        >>> result["upper"]
        shape: (50,)
        Series: 'bb_upper_20' [...]
    """
    if column not in df.columns:
        warnings.warn(
            f"Column '{column}' not found in DataFrame. Returning empty result."
        )
        empty_series = Series("bb_upper_20")
        return {
            "upper": empty_series,
            "middle": empty_series,
            "lower": empty_series,
        }

    if period <= 0:
        warnings.warn(f"Invalid period {period}. Using absolute value.")
        period = abs(period)

    if num_std <= 0:
        warnings.warn(f"Invalid num_std {num_std}. Using absolute value.")
        num_std = abs(num_std)

    if df.height < period:
        warnings.warn(
            f"Insufficient data: {df.height} rows for period {period}. "
            f"Need at least {period} data points."
        )
        empty_series = Series(f"bb_upper_{period}")
        return {
            "upper": empty_series,
            "middle": empty_series,
            "lower": empty_series,
        }

    # Calculate middle band (SMA)
    middle_band = calculate_sma(df, column, period)
    middle_band = middle_band.rename(f"bb_middle_{period}")

    # Calculate rolling standard deviation
    std_series = df.get_column(column).rolling_std(period).rename(f"bb_std_{period}")

    # Calculate upper and lower bands
    upper_band = (middle_band + num_std * std_series).alias(f"bb_upper_{period}")
    lower_band = (middle_band - num_std * std_series).alias(f"bb_lower_{period}")

    result: BollingerBandsResult = {
        "upper": upper_band,
        "middle": middle_band,
        "lower": lower_band,
    }

    logger.debug(
        f"Calculated Bollinger Bands({period}, {num_std}): {len(upper_band)} values"
    )
    return result


# =============================================================================
# VOLUME FEATURES
# =============================================================================


def calculate_volume_features(
    df: DataFrame,
    column: str = "volume",
    period: int = 20,
) -> VolumeFeaturesResult:
    """
    Calculate volume-based features.

    Computes features related to trading volume:
    - volume_sma: Simple moving average of volume
    - volume_ratio: Current volume / volume SMA (indicates volume spikes)

    Args:
        df: Polars DataFrame with stock data.
        column: Column name for volume (default: "volume").
        period: Number of periods for volume SMA (default: 20).

    Returns:
        Dictionary with keys:
            - "volume_sma": Volume SMA Series
            - "volume_ratio": Volume ratio Series

    Examples:
        >>> df = DataFrame({"volume": [1000, 2000, 3000, 4000, 5000] * 5})
        >>> result = calculate_volume_features(df, period=20)
        >>> result["volume_sma"]
        shape: (50,)
        Series: 'volume_sma_20' [...]
    """
    if column not in df.columns:
        warnings.warn(
            f"Column '{column}' not found in DataFrame. Returning empty result."
        )
        empty_series = Series("volume_sma_20")
        return {
            "volume_sma": empty_series,
            "volume_ratio": empty_series,
        }

    if period <= 0:
        warnings.warn(f"Invalid period {period}. Using absolute value.")
        period = abs(period)

    if df.height < period:
        warnings.warn(
            f"Insufficient data: {df.height} rows for period {period}. "
            f"Need at least {period} data points."
        )
        empty_series = Series(f"volume_sma_{period}")
        return {
            "volume_sma": empty_series,
            "volume_ratio": empty_series,
        }

    # Calculate volume SMA
    volume_sma = calculate_sma(df, column, period)
    volume_sma = volume_sma.rename(f"volume_sma_{period}")

    # Calculate volume ratio
    current_volume = df.get_column(column)
    volume_ratio_series = (current_volume / volume_sma).alias(f"volume_ratio_{period}")

    # Handle division by zero and inf values
    volume_ratio_series = volume_ratio_series.map_elements(
        lambda x: 1.0 if x == float("inf") or x != x else x,  # x != x checks for NaN
        return_dtype=float,
    )

    result: VolumeFeaturesResult = {
        "volume_sma": volume_sma,
        "volume_ratio": volume_ratio_series,
    }

    logger.debug(f"Calculated Volume Features({period}): {len(volume_sma)} values")
    return result


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "calculate_sma",
    "calculate_ema",
    "calculate_rsi",
    "calculate_macd",
    "calculate_bollinger_bands",
    "calculate_volume_features",
    "MACDResult",
    "BollingerBandsResult",
    "VolumeFeaturesResult",
]
