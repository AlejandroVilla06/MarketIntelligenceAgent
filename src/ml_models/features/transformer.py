"""
Feature Transformer for ML Pipeline
=============================

Coordinates all technical indicator calculations and adds them to DataFrames.

Usage:
    from src.ml_models.features import FeatureEngineer

    transformer = FeatureEngineer(sma_period=20, rsi_period=14)
    df_with_features = transformer.transform(stock_df)
"""

from __future__ import annotations

from dataclasses import dataclass

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
from src.utils import get_logger


# =============================================================================
# LOGGING
# =============================================================================

logger = get_logger(__name__)


# =============================================================================
# FEATURE ENGINEER
# =============================================================================


@dataclass
class FeatureEngineer:
    """
    Computes technical indicators from OHLCV stock data.

    This class coordinates the calculation of all technical indicators and
    adds them as new columns to the input DataFrame. It provides a convenient interface
    for generating features for ML models.

    Attributes:
        sma_period: Number of periods for Simple Moving Average (default: 20).
        ema_period: Number of periods for Exponential Moving Average (default: 12).
        rsi_period: Number of periods for RSI calculation (default: 14).
        macd_fast: Fast EMA period for MACD (default: 12).
        macd_slow: Slow EMA period for MACD (default: 26).
        macd_signal: Signal line EMA period for MACD (default: 9).
        bb_period: Number of periods for Bollinger Bands (default: 20).
        bb_std: Number of standard deviations for Bollinger Bands (default: 2.0).
        volume_period: Number of periods for volume features (default: 20).

    Usage:
        >>> df = DataFrame({
        ...     "date": [datetime(2024, 1, i) for i in range(1, 31)],
        ...     "open": [100.0] * 30,
        ...     "high": [105.0] * 30,
        ...     "low": [95.0] * 30,
        ...     "close": [100.0 + i for i in range(30)],
        ...     "volume": [1000000] * 30,
        ... })
        >>> transformer = FeatureEngineer(sma_period=20, rsi_period=14)
        >>> df_features = transformer.transform(df)
        >>> print(df_features.columns)
        ['date', 'open', 'high', 'low', 'close', 'volume', 'sma_20', ...]
    """

    sma_period: int = 20
    ema_period: int = 12
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bb_period: int = 20
    bb_std: float = 2.0
    volume_period: int = 20

    # Required columns for input DataFrame
    REQUIRED_COLUMNS: list[str] = (
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
    )

    # Optional columns that can be used for calculations
    OPTIONAL_COLUMNS: list[str] = (
        "symbol",
        "adj_close",
    )

    def __post_init__(self) -> None:
        """Validate period parameters after initialization."""
        # Ensure periods are positive
        self.sma_period = max(1, abs(self.sma_period))
        self.ema_period = max(1, abs(self.ema_period))
        self.rsi_period = max(1, abs(self.rsi_period))
        self.macd_fast = max(1, abs(self.macd_fast))
        self.macd_slow = max(1, abs(self.macd_slow))
        self.macd_signal = max(1, abs(self.macd_signal))
        self.bb_period = max(1, abs(self.bb_period))
        self.bb_std = abs(self.bb_std)
        self.volume_period = max(1, abs(self.volume_period))

        # Ensure macd_slow > macd_fast
        if self.macd_slow <= self.macd_fast:
            logger.warning(
                f"macd_slow ({self.macd_slow}) should be > macd_fast ({self.macd_fast}). "
                f"Swapping values."
            )
            self.macd_fast, self.macd_slow = self.macd_slow, self.macd_fast

        logger.info(
            f"FeatureEngineer initialized with periods: "
            f"SMA={self.sma_period}, EMA={self.ema_period}, RSI={self.rsi_period}, "
            f"MACD=({self.macd_fast},{self.macd_slow},{self.macd_signal}), "
            f"BB=({self.bb_period},{self.bb_std}), "
            f"Volume={self.volume_period}"
        )

    def validate_input(self, df: DataFrame) -> tuple[bool, list[str]]:
        """
        Validate that input DataFrame has required columns.

        Args:
            df: Polars DataFrame to validate.

        Returns:
            Tuple of (is_valid, list of error messages).
        """
        errors: list[str] = []

        # Check for empty DataFrame
        if df.height == 0:
            errors.append("DataFrame is empty")
            return False, errors

        # Check for required columns
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")

        # Warn about optional columns
        missing_optional = [col for col in self.OPTIONAL_COLUMNS if col not in df.columns]
        if missing_optional:
            logger.debug(f"Optional columns not found: {missing_optional}")

        return len(errors) == 0, errors

    def transform(self, df: DataFrame) -> DataFrame:
        """
        Add all technical indicators as columns to the DataFrame.

        This method computes all configured technical indicators and adds them
        as new columns to the input DataFrame while preserving original columns.

        Args:
            df: DataFrame with columns: date, open, high, low, close, volume
                (and optionally: symbol, adj_close)

        Returns:
            DataFrame with additional columns:
                - sma_{period}: Simple Moving Average
                - ema_{period}: Exponential Moving Average
                - rsi_{period}: Relative Strength Index
                - macd_{fast}_{slow}: MACD line
                - macd_signal_{signal_period}: Signal line
                - macd_hist_{fast}_{slow}: MACD histogram
                - bb_upper_{period}: Bollinger Upper Band
                - bb_middle_{period}: Bollinger Middle Band (SMA)
                - bb_lower_{period}: Bollinger Lower Band
                - volume_sma_{period}: Volume SMA
                - volume_ratio_{period}: Volume Ratio

        Raises:
            ValueError: If DataFrame is empty or missing required columns.

        Examples:
            >>> df = DataFrame({
            ...     "date": [datetime(2024, 1, i) for i in range(1, 31)],
            ...     "open": [100.0] * 30,
            ...     "high": [105.0] * 30,
            ...     "low": [95.0] * 30,
            ...     "close": [100.0 + i for i in range(30)],
            ...     "volume": [1000000] * 30,
            ... })
            >>> transformer = FeatureEngineer(sma_period=20, rsi_period=14)
            >>> df_features = transformer.transform(df)
            >>> print(df_features.columns)
            ['date', 'open', 'high', 'low', 'close', 'volume', 'sma_20', ...]
        """
        # Validate input
        is_valid, errors = self.validate_input(df)
        if not is_valid:
            error_msg = f"Invalid input DataFrame: {'; '.join(errors)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Transforming DataFrame with {df.height} rows")

        # Create result DataFrame with original columns
        result_df = df.clone()

        # 1. Calculate SMA
        logger.debug(f"Calculating SMA with period {self.sma_period}")
        sma_series = calculate_sma(df, "close", self.sma_period)
        if sma_series.len() > 0:
            result_df = result_df.with_columns(sma_series)

        # 2. Calculate EMA
        logger.debug(f"Calculating EMA with period {self.ema_period}")
        ema_series = calculate_ema(df, "close", self.ema_period)
        if ema_series.len() > 0:
            result_df = result_df.with_columns(ema_series)

        # 3. Calculate RSI
        logger.debug(f"Calculating RSI with period {self.rsi_period}")
        rsi_series = calculate_rsi(df, "close", self.rsi_period)
        if rsi_series.len() > 0:
            result_df = result_df.with_columns(rsi_series)

        # 4. Calculate MACD
        logger.debug(
            f"Calculating MACD with periods ({self.macd_fast}, {self.macd_slow}, {self.macd_signal})"
        )
        macd_result = calculate_macd(
            df,
            "close",
            self.macd_fast,
            self.macd_slow,
            self.macd_signal,
        )
        for key, series in macd_result.items():
            if series.len() > 0:
                result_df = result_df.with_columns(series)

        # 5. Calculate Bollinger Bands
        logger.debug(
            f"Calculating Bollinger Bands with period {self.bb_period}, std {self.bb_std}"
        )
        bb_result = calculate_bollinger_bands(
            df,
            "close",
            self.bb_period,
            self.bb_std,
        )
        for key, series in bb_result.items():
            if series.len() > 0:
                result_df = result_df.with_columns(series)

        # 6. Calculate Volume Features
        logger.debug(f"Calculating Volume Features with period {self.volume_period}")
        volume_result = calculate_volume_features(df, "volume", self.volume_period)
        for key, series in volume_result.items():
            if series.len() > 0:
                result_df = result_df.with_columns(series)

        logger.info(
            f"Transformation complete. Added {result_df.width - df.width} new columns. "
            f"Total columns: {result_df.width}"
        )

        return result_df

    def get_feature_columns(self) -> list[str]:
        """
        Get list of feature column names that will be added by transform().

        Returns:
            List of column names for all computed features.
        """
        return [
            f"sma_{self.sma_period}",
            f"ema_{self.ema_period}",
            f"rsi_{self.rsi_period}",
            f"macd_{self.macd_fast}_{self.macd_slow}",
            f"macd_signal_{self.macd_signal}",
            f"macd_hist_{self.macd_fast}_{self.macd_slow}",
            f"bb_upper_{self.bb_period}",
            f"bb_middle_{self.bb_period}",
            f"bb_lower_{self.bb_period}",
            f"volume_sma_{self.volume_period}",
            f"volume_ratio_{self.volume_period}",
        ]


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "FeatureEngineer",
]