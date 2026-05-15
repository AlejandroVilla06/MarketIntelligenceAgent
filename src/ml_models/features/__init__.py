"""
Feature Engineering Module for Market Intelligence Agent
============================================

This module provides technical indicator calculations and feature transformation
for stock market data.

Usage:
    from src.ml_models.features import (
        calculate_sma,
        calculate_ema,
        calculate_rsi,
        calculate_macd,
        calculate_bollinger_bands,
        calculate_volume_features,
        FeatureEngineer,
    )

    # Calculate individual indicators
    sma = calculate_sma(df, column="close", period=20)

    # Or use FeatureEngineer for all indicators at once
    transformer = FeatureEngineer(sma_period=20, rsi_period=14)
    df_with_features = transformer.transform(stock_df)
"""

from __future__ import annotations

# Import indicator functions
from src.ml_models.features.indicators import (
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
    calculate_volume_features,
)

# Import FeatureEngineer class
from src.ml_models.features.transformer import FeatureEngineer


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Indicator functions
    "calculate_sma",
    "calculate_ema",
    "calculate_rsi",
    "calculate_macd",
    "calculate_bollinger_bands",
    "calculate_volume_features",
    # Feature transformer
    "FeatureEngineer",
]